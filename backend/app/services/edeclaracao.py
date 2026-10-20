from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal
from typing import Callable

from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from app.models.documento import Documento, EstadoDocumento, TipoDocumentoFiscal
from app.models.empresa import Empresa

MAX_BYTES = 2 * 1024 * 1024  # 2 MB


# ---------- Recolha de documentos ----------


def obter_documentos_periodo(db: Session, ano: int, mes: int) -> list[Documento]:
    """
    Documentos FISCAIS do periodo, finalizados ou anulados.
    Rascunhos e nao fiscais ficam de fora (nao declaram).
    """
    inicio = date(ano, mes, 1)
    if mes == 12:
        fim = date(ano + 1, 1, 1)
    else:
        fim = date(ano, mes + 1, 1)

    return (
        db.query(Documento)
        .filter(
            Documento.fiscal.is_(True),
            Documento.estado.in_(
                [EstadoDocumento.FINALIZADO, EstadoDocumento.ANULADO]
            ),
            Documento.data_documento >= inicio,
            Documento.data_documento < fim,
        )
        .order_by(Documento.data_documento, Documento.id)
        .all()
    )


# ---------- XML ----------


def _dec_str(v: Decimal | None) -> str:
    if v is None:
        return "0.00"
    return f"{v:.2f}"


def _montar_xml(docs: list[Documento], empresa: Empresa | None, ano: int, mes: int) -> bytes:
    root = ET.Element("DeclaracaoMensal")
    root.set("versao", "1.0")
    root.set(
        "aviso",
        "Estrutura provisoria - sujeita a confirmacao pela AT (Aviso 40/AT/DGI/2025)",
    )

    # Cabecalho
    cab = ET.SubElement(root, "Cabecalho")
    ET.SubElement(cab, "Nuit").text = (empresa.nuit if empresa else "")
    ET.SubElement(cab, "Designacao").text = (empresa.designacao if empresa else "")
    periodo = ET.SubElement(cab, "Periodo")
    ET.SubElement(periodo, "Ano").text = str(ano)
    ET.SubElement(periodo, "Mes").text = str(mes)
    ET.SubElement(cab, "DataGeracao").text = datetime.utcnow().isoformat(timespec="seconds")
    ET.SubElement(cab, "VersaoLayout").text = "1.0"

    # Documentos
    docs_el = ET.SubElement(root, "Documentos")
    soma_base = Decimal("0")
    soma_iva = Decimal("0")
    soma_total = Decimal("0")

    for d in docs:
        doc_el = ET.SubElement(docs_el, "Documento")
        ET.SubElement(doc_el, "TipoDocumento").text = d.tipo_documento.value
        ET.SubElement(doc_el, "SerieId").text = str(d.serie_id)
        ET.SubElement(doc_el, "Numero").text = str(d.numero)
        ET.SubElement(doc_el, "NumeroFormatado").text = d.numero_formatado
        ET.SubElement(doc_el, "Data").text = d.data_documento.isoformat()
        ET.SubElement(doc_el, "NuitCliente").text = d.cliente_nuit or ""
        ET.SubElement(doc_el, "NomeCliente").text = d.cliente_nome or ""
        ET.SubElement(doc_el, "BaseTributavel").text = _dec_str(d.subtotal)
        ET.SubElement(doc_el, "Iva").text = _dec_str(d.total_iva)
        ET.SubElement(doc_el, "Total").text = _dec_str(d.total)
        ET.SubElement(doc_el, "Estado").text = d.estado.value
        ET.SubElement(doc_el, "Hash").text = d.hash or ""

        soma_base += d.subtotal
        soma_iva += d.total_iva
        soma_total += d.total

    # Totais
    totais = ET.SubElement(root, "Totais")
    ET.SubElement(totais, "NumeroDocumentos").text = str(len(docs))
    ET.SubElement(totais, "SomaBase").text = _dec_str(soma_base)
    ET.SubElement(totais, "SomaIva").text = _dec_str(soma_iva)
    ET.SubElement(totais, "SomaTotal").text = _dec_str(soma_total)

    tree = ET.ElementTree(root)
    buf = io.BytesIO()
    tree.write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue()


# ---------- XLSX ----------


def _montar_xlsx(docs: list[Documento], empresa: Empresa | None, ano: int, mes: int) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "e-Declaracao"

    bold = Font(bold=True)

    # Cabecalho
    ws["A1"] = "Declaracao mensal de faturas"
    ws["A1"].font = bold
    ws["A2"] = "NUIT emitente"
    ws["B2"] = (empresa.nuit if empresa else "")
    ws["A3"] = "Designacao"
    ws["B3"] = (empresa.designacao if empresa else "")
    ws["A4"] = "Periodo"
    ws["B4"] = f"{ano}-{mes:02d}"
    ws["A5"] = "Data geracao"
    ws["B5"] = datetime.utcnow().isoformat(timespec="seconds")
    ws["A6"] = "Versao layout"
    ws["B6"] = "1.0"

    # Cabecalho da tabela
    headers = [
        "Tipo", "SerieId", "Numero", "NumeroFormatado", "Data",
        "NUIT Cliente", "Nome Cliente", "Base", "IVA", "Total", "Estado", "Hash",
    ]
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=8, column=col, value=h)
        cell.font = bold

    # Linhas
    soma_base = Decimal("0")
    soma_iva = Decimal("0")
    soma_total = Decimal("0")
    row = 9
    for d in docs:
        ws.cell(row=row, column=1, value=d.tipo_documento.value)
        ws.cell(row=row, column=2, value=d.serie_id)
        ws.cell(row=row, column=3, value=d.numero)
        ws.cell(row=row, column=4, value=d.numero_formatado)
        ws.cell(row=row, column=5, value=d.data_documento.isoformat())
        ws.cell(row=row, column=6, value=d.cliente_nuit or "")
        ws.cell(row=row, column=7, value=d.cliente_nome or "")
        ws.cell(row=row, column=8, value=float(d.subtotal))
        ws.cell(row=row, column=9, value=float(d.total_iva))
        ws.cell(row=row, column=10, value=float(d.total))
        ws.cell(row=row, column=11, value=d.estado.value)
        ws.cell(row=row, column=12, value=d.hash or "")
        soma_base += d.subtotal
        soma_iva += d.total_iva
        soma_total += d.total
        row += 1

    # Totais
    row += 1
    ws.cell(row=row, column=1, value="Numero de documentos").font = bold
    ws.cell(row=row, column=2, value=len(docs))
    row += 1
    ws.cell(row=row, column=1, value="Soma Base").font = bold
    ws.cell(row=row, column=2, value=float(soma_base))
    row += 1
    ws.cell(row=row, column=1, value="Soma IVA").font = bold
    ws.cell(row=row, column=2, value=float(soma_iva))
    row += 1
    ws.cell(row=row, column=1, value="Soma Total").font = bold
    ws.cell(row=row, column=2, value=float(soma_total))

    # Larguras
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["G"].width = 30
    ws.column_dimensions["L"].width = 40

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------- Divisao por tamanho ----------


def _dividir_por_tamanho(
    docs: list[Documento],
    gerar_fn: Callable[[list[Documento]], bytes],
    max_bytes: int = MAX_BYTES,
) -> list[bytes]:
    """
    Tenta gerar tudo de uma vez. Se exceder max_bytes, encontra o maior
    chunk que cabe e divide. Chunks sao sempre subconjuntos contiguos
    (a ordem original preserva-se).
    """
    if not docs:
        return [gerar_fn([])]

    conteudo = gerar_fn(docs)
    if len(conteudo) <= max_bytes:
        return [conteudo]

    if len(docs) == 1:
        return [conteudo]  # caso extremo: 1 documento ja excede 2MB

    # Encontra o maior chunk que cabe (binary search descendente)
    chunk = max(1, len(docs) // 2)
    while chunk > 1:
        test = gerar_fn(docs[:chunk])
        if len(test) <= max_bytes:
            break
        chunk //= 2

    partes: list[bytes] = []
    i = 0
    while i < len(docs):
        sub = docs[i : i + chunk]
        partes.append(gerar_fn(sub))
        i += chunk
    return partes


# ---------- API publica do servico ----------


def gerar_edeclaracao(
    docs: list[Documento],
    empresa: Empresa | None,
    ano: int,
    mes: int,
    formato: str,
) -> list[bytes]:
    if formato == "xml":
        fn = lambda sub: _montar_xml(sub, empresa, ano, mes)
    elif formato == "xlsx":
        fn = lambda sub: _montar_xlsx(sub, empresa, ano, mes)
    else:
        raise ValueError(f"Formato nao suportado: {formato}")

    return _dividir_por_tamanho(docs, fn)