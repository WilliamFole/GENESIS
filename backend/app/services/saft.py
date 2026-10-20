from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.documento import Documento, EstadoDocumento, TipoDocumentoFiscal
from app.models.empresa import Empresa
from app.models.imposto import Imposto

# Estrutura PROVISORIA inspirada no SAF-T OCDE (AuditFile).
# A AT mocambicana ainda nao publicou XSD nem estrutura especifica.
# Quando publicar, este modulo e o unico que precisa de ser adaptado.


def _periodo(ano: int, mes: int) -> tuple[date, date]:
    inicio = date(ano, mes, 1)
    fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, fim


def _fmt(v: Decimal | None) -> str:
    return f"{v:.2f}" if v is not None else "0.00"


def gerar_saft(db: Session, ano: int, mes: int) -> bytes:
    inicio, fim = _periodo(ano, mes)

    empresa = db.query(Empresa).order_by(Empresa.id).first()
    docs = (
        db.query(Documento)
        .filter(
            Documento.fiscal.is_(True),
            Documento.estado.in_(
                [EstadoDocumento.FINALIZADO, EstadoDocumento.ANULADO]
            ),
            Documento.data_documento >= inicio,
            Documento.data_documento < fim,
        )
        .order_by(Documento.data_documento, Documento.numero)
        .all()
    )

    # root + comentario
    root = ET.Element("AuditFile")
    root.set("xmlns", "urn:OECD:StandardAuditFile-Tax:20240101")
    root.set("versao", "provisorio-1.0")
    root.append(
        ET.Comment(
            " Estrutura PROVISORIA, aguarda publicacao do XSD pela AT. "
            "Baseada no SAF-T OCDE. "
        )
    )

    # Header
    header = ET.SubElement(root, "Header")
    ET.SubElement(header, "AuditFileVersion").text = "1.0-provisorio"
    ET.SubElement(header, "CompanyID").text = (empresa.designacao if empresa else "")
    ET.SubElement(header, "TaxRegistrationNumber").text = (empresa.nuit if empresa else "")
    ET.SubElement(header, "TaxAccountingBasis").text = "F"
    ET.SubElement(header, "CompanyName").text = (empresa.designacao if empresa else "")
    if empresa:
        ET.SubElement(header, "BusinessName").text = empresa.designacao
        ET.SubElement(header, "CompanyAddress").text = empresa.morada
    ET.SubElement(header, "FiscalYear").text = str(ano)
    ET.SubElement(header, "StartDate").text = inicio.isoformat()
    ET.SubElement(header, "EndDate").text = (fim.replace(day=1)).isoformat()
    ET.SubElement(header, "CurrencyCode").text = "MZN"
    ET.SubElement(header, "DateCreated").text = datetime.utcnow().date().isoformat()
    ET.SubElement(header, "ProductID").text = "Genesis/SGE-Faturacao"
    ET.SubElement(header, "ProductVersion").text = "0.1.0"

    # MasterFiles -> Customers
    master = ET.SubElement(root, "MasterFiles")
    customers = ET.SubElement(master, "Customer")

    # Clientes referenciados no periodo (ou todos se poucos)
    clientes_ids = sorted({d.cliente_id for d in docs if d.cliente_id})
    if clientes_ids:
        clientes = db.query(Cliente).filter(Cliente.id.in_(clientes_ids)).all()
    else:
        clientes = []

    for c in clientes:
        c_el = ET.SubElement(customers, "Customer")
        ET.SubElement(c_el, "CustomerID").text = str(c.id)
        ET.SubElement(c_el, "AccountID").text = "Desconhecido"
        ET.SubElement(c_el, "CustomerTaxID").text = c.nuit
        ET.SubElement(c_el, "CompanyName").text = c.nome
        ET.SubElement(c_el, "BillingAddress").text = c.morada

    # MasterFiles -> TaxTable
    impostos = db.query(Imposto).all()
    taxtable = ET.SubElement(master, "TaxTable")
    for i in impostos:
        t_el = ET.SubElement(taxtable, "TaxTableEntry")
        ET.SubElement(t_el, "TaxType").text = "IVA"
        ET.SubElement(t_el, "TaxCountryRegion").text = "MZ"
        ET.SubElement(t_el, "TaxCode").text = i.codigo
        ET.SubElement(t_el, "Description").text = i.descricao
        ET.SubElement(t_el, "TaxPercentage").text = f"{i.percentagem:.2f}"

    # SourceDocuments -> SalesInvoices -> Invoice
    src = ET.SubElement(root, "SourceDocuments")
    sales = ET.SubElement(src, "SalesInvoices")
    ET.SubElement(sales, "NumberOfEntries").text = str(len(docs))
    ET.SubElement(sales, "TotalDebit").text = _fmt(sum((d.total for d in docs), Decimal("0")))
    ET.SubElement(sales, "TotalCredit").text = "0.00"

    for d in docs:
        inv = ET.SubElement(sales, "Invoice")
        ET.SubElement(inv, "InvoiceNo").text = d.numero_formatado
        ET.SubElement(inv, "Hash").text = d.hash or ""
        ET.SubElement(inv, "InvoiceStatus").text = "N" if d.estado == EstadoDocumento.FINALIZADO else "A"
        ET.SubElement(inv, "InvoiceDate").text = d.data_documento.isoformat()
        ET.SubElement(inv, "InvoiceType").text = d.tipo_documento.value
        ET.SubElement(inv, "SystemEntryDate").text = (
            d.finalizado_em.isoformat() if d.finalizado_em else d.criado_em.isoformat()
        )
        ET.SubElement(inv, "CustomerID").text = str(d.cliente_id or "")
        ET.SubElement(inv, "CustomerTaxID").text = d.cliente_nuit or ""
        ET.SubElement(inv, "CustomerName").text = d.cliente_nome or ""
        ET.SubElement(inv, "DocumentoOrigemID").text = (
            str(d.documento_origem_id) if d.documento_origem_id else ""
        )

        linha_el = ET.SubElement(inv, "Line")
        for l in d.linhas:
            li = ET.SubElement(linha_el, "Line")
            ET.SubElement(li, "LineNumber").text = str(l.id)
            ET.SubElement(li, "ProductCode").text = l.codigo
            ET.SubElement(li, "ProductDescription").text = l.descricao
            ET.SubElement(li, "Quantity").text = str(l.quantidade)
            ET.SubElement(li, "UnitOfMeasure").text = l.unidade
            ET.SubElement(li, "UnitPrice").text = _fmt(l.preco_unitario)
            ET.SubElement(li, "CreditAmount").text = _fmt(l.base_tributavel)
            # Tax
            tax = ET.SubElement(li, "Tax")
            ET.SubElement(tax, "TaxType").text = "IVA"
            ET.SubElement(tax, "TaxCountryRegion").text = "MZ"
            ET.SubElement(tax, "TaxPercentage").text = f"{l.taxa_iva:.2f}"
            ET.SubElement(li, "TaxPayable").text = _fmt(l.valor_iva)

        # DocumentTotals
        tot = ET.SubElement(inv, "DocumentTotals")
        ET.SubElement(tot, "TaxPayable").text = _fmt(d.total_iva)
        ET.SubElement(tot, "NetTotal").text = _fmt(d.subtotal)
        ET.SubElement(tot, "GrossTotal").text = _fmt(d.total)

    tree = ET.ElementTree(root)
    buf = io.BytesIO()
    tree.write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue()