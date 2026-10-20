from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.documento import Documento, EstadoDocumento, TipoDocumentoFiscal
from app.models.empresa import Empresa
from app.models.pagamento import Pagamento
from app.models.utilizador import Utilizador
from app.services import relatorios, relatorios_pdf

router = APIRouter(prefix="/api/relatorios", tags=["relatorios"])


def _gerar_ficheiro(
    dados: list[dict], headers: list[str], titulo: str,
    formato: str, nome_base: str,
) -> Response:
    if formato == "csv":
        return Response(
            relatorios.gerar_csv(dados, headers),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{nome_base}.csv"'},
        )
    if formato == "xlsx":
        return Response(
            relatorios.gerar_excel(dados, headers, titulo),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{nome_base}.xlsx"'},
        )
    if formato == "pdf":
        return Response(
            relatorios.gerar_pdf_relatorio(dados, headers, titulo),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nome_base}.pdf"'},
        )
    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato invalido.")


# ============ VENDAS ============

@router.get("/vendas")
def obter_vendas(
    data_inicio: date,
    data_fim: date,
    cliente_id: int | None = None,
    artigo_id: int | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    return relatorios.relatorio_vendas(db, data_inicio, data_fim, cliente_id, artigo_id)


@router.get("/vendas/exportar/{formato}")
def exportar_vendas(
    formato: str,
    data_inicio: date,
    data_fim: date,
    cliente_id: int | None = None,
    artigo_id: int | None = None,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    res = relatorios.relatorio_vendas(db, data_inicio, data_fim, cliente_id, artigo_id)
    
    tipo_nome = "vendas"
    nome = relatorios.nome_extrato(tipo_nome, data_inicio, data_fim, formato)

    if formato == "pdf":
        empresa = db.query(Empresa).order_by(Empresa.id).first()
        filtros = {
            "periodo": f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
        }
        pdf_bytes = relatorios_pdf.gerar_relatorio_vendas_pdf(
            empresa, filtros, res, user,
        )
        return Response(
            pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nome}"'},
        )

    # Para CSV e Excel, mantém o formato antigo
    dados = [
        {
            "Cliente": c["nome"],
            "Total Bruto (MZN)": f"{c['bruto']:.2f}",
            "Total Líquido (MZN)": f"{c['liquido']:.2f}",
            "Total IVA (MZN)": f"{c['iva']:.2f}",
        }
        for c in res["por_cliente"]
    ]
    headers = ["Cliente", "Total Bruto (MZN)", "Total Líquido (MZN)", "Total IVA (MZN)"]
    titulo = relatorios.nome_extrato("vendas", data_inicio, data_fim, "")
    return _gerar_ficheiro(dados, headers, titulo, formato, nome.rsplit(".", 1)[0])

# ============ DOCUMENTOS ============

@router.get("/documentos")
def obter_documentos(
    data_inicio: date,
    data_fim: date,
    tipo: str | None = None,
    serie_id: int | None = None,
    estado: str | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    docs = relatorios.relatorio_documentos(db, data_inicio, data_fim, tipo, serie_id, estado)
    return [
        {
            "id": d.id,
            "tipo": d.tipo_documento.value,
            "numero": d.numero_formatado or "—",
            "data": d.data_documento,
            "cliente": d.cliente_nome,
            "estado": d.estado.value,
            "total": d.total,
        }
        for d in docs
    ]


@router.get("/documentos/exportar/{formato}")
def exportar_documentos(
    formato: str,
    data_inicio: date,
    data_fim: date,
    tipo: str | None = None,
    serie_id: int | None = None,
    estado: str | None = None,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    docs = relatorios.relatorio_documentos(db, data_inicio, data_fim, tipo, serie_id, estado)

    # ===== PDF: layout Extrato de Faturas =====
    if formato == "pdf":
        empresa = db.query(Empresa).order_by(Empresa.id).first()
        hoje = date.today()

        enriched: list[dict] = []
        resumo = {
            "pagas":    {"n": 0, "total": Decimal("0")},
            "abertas":  {"n": 0, "total": Decimal("0")},
            "vencidas": {"n": 0, "total": Decimal("0")},
        }
        totais = {"liquido": Decimal("0"), "iva": Decimal("0"), "total": Decimal("0")}

        for d in docs:
            if d.tipo_documento in (
                TipoDocumentoFiscal.NC,
                TipoDocumentoFiscal.ND,
                TipoDocumentoFiscal.RC,
                TipoDocumentoFiscal.COT,
                TipoDocumentoFiscal.PRO,
                TipoDocumentoFiscal.GR,
            ):
                continue

            pago = db.query(func.coalesce(func.sum(Pagamento.valor), 0)).filter(
                Pagamento.documento_id == d.id
            ).scalar()
            creditado = relatorios._calcular_credito(db, d.id)
            saldo = Decimal(d.total) - Decimal(pago) - creditado

            if saldo <= 0:
                est = "Paga"
                resumo["pagas"]["n"] += 1
                resumo["pagas"]["total"] += d.total
            elif d.data_vencimento and d.data_vencimento < hoje:
                est = "Vencida"
                resumo["vencidas"]["n"] += 1
                resumo["vencidas"]["total"] += d.total
            else:
                est = "Em aberto"
                resumo["abertas"]["n"] += 1
                resumo["abertas"]["total"] += d.total

            liquido = Decimal(d.subtotal) - Decimal(d.desconto_global_valor)
            totais["liquido"] += liquido
            totais["iva"] += d.total_iva
            totais["total"] += d.total

            enriched.append({
                "documento": f"{d.tipo_documento.value} {d.numero_formatado or '—'}",
                "data": d.data_documento.strftime("%d/%m/%Y"),
                "vencimento": d.data_vencimento.strftime("%d/%m/%Y") if d.data_vencimento else "—",
                "cliente": d.cliente_nome or "—",
                "liquido": liquido,
                "iva": d.total_iva,
                "total": d.total,
                "estado": est,
            })

        filtros = {
            "periodo": f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
            "cliente": "Todos",
            "estado": estado or "Todos",
        }
        pdf_bytes = relatorios_pdf.gerar_extrato_faturas_pdf(
            empresa, filtros, enriched, resumo, totais, user,
        )
        tipo_extrato = tipo.lower() if tipo else "faturas"
        nome = relatorios.nome_extrato(tipo_extrato, data_inicio, data_fim, "pdf")
        return Response(
            pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nome}"'},
        )

    # ===== CSV/XLSX =====
    dados = [
        {
            "Tipo": d.tipo_documento.value,
            "Nº": d.numero_formatado or "—",
            "Data": d.data_documento.strftime("%d/%m/%Y"),
            "Cliente": d.cliente_nome,
            "Estado": d.estado.value,
            "Total": f"{d.total:.2f}",
        }
        for d in docs
    ]
    headers = ["Tipo", "Nº", "Data", "Cliente", "Estado", "Total"]
    tipo_extrato = tipo.lower() if tipo else "documentos"
    titulo = relatorios.nome_extrato(tipo_extrato, data_inicio, data_fim, "")
    nome = relatorios.nome_extrato(tipo_extrato, data_inicio, data_fim, formato)
    return _gerar_ficheiro(dados, headers, titulo, formato, nome.rsplit(".", 1)[0])


# ============ NUMERAÇÃO ============

@router.get("/numeracao")
def obter_numeracao(
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    return relatorios.relatorio_numeracao(db)


# ============ SALDOS ============

@router.get("/saldos")
def obter_saldos(
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    return relatorios.relatorio_saldos(db)


# ============ EXTRATO CLIENTE ============

@router.get("/extrato-cliente/{cliente_id}")
def obter_extrato_cliente(
    cliente_id: int,
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    try:
        return relatorios.relatorio_extrato_cliente(db, cliente_id, data_inicio, data_fim)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))


@router.get("/extrato-cliente/{cliente_id}/exportar/{formato}")
def exportar_extrato_cliente(
    cliente_id: int,
    formato: str,
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    try:
        res = relatorios.relatorio_extrato_cliente(db, cliente_id, data_inicio, data_fim)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))

    tipo_nome = f"cliente {res['cliente']['numero_formatado']} - {res['cliente']['nome']}"
    nome = relatorios.nome_extrato(tipo_nome, data_inicio, data_fim, formato, prefixo="Extrato do")

    if formato == "pdf":
        empresa = db.query(Empresa).order_by(Empresa.id).first()
        cliente = db.get(Cliente, cliente_id)
        if not cliente:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Cliente nao encontrado"
            )
        aging = relatorios.calcular_aging_cliente(db, cliente_id)
        pdf_bytes = relatorios_pdf.gerar_extrato_cliente_pdf(
            empresa, cliente, res, aging, user,
        )
        return Response(
            pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nome}"'},
        )

    dados = [
        {
            "Data": m["data"].strftime("%d/%m/%Y"),
            "Tipo": m["tipo"],
            "Nº": m["numero"],
            "Descricao": m["descricao"],
            "Debito": f"{m['debito']:.2f}",
            "Credito": f"{m['credito']:.2f}",
            "Saldo": f"{m['saldo']:.2f}",
        }
        for m in res["movimentos"]
    ]
    headers = ["Data", "Tipo", "Nº", "Descricao", "Debito", "Credito", "Saldo"]
    titulo = relatorios.nome_extrato(tipo_nome, data_inicio, data_fim, "", prefixo="Extrato do")
    return _gerar_ficheiro(dados, headers, titulo, formato, nome.rsplit(".", 1)[0])


# ============ EXTRATO GERAL (TODOS OS CLIENTES) ============

@router.get("/extrato-clientes/geral")
def obter_extrato_clientes_geral(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    return relatorios.relatorio_extrato_clientes_geral(db, data_inicio, data_fim)


@router.get("/extrato-clientes/geral/exportar/{formato}")
def exportar_extrato_clientes_geral(
    formato: str,
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    res = relatorios.relatorio_extrato_clientes_geral(db, data_inicio, data_fim)

    tipo_nome = "clientes"
    nome = relatorios.nome_extrato(
        tipo_nome, data_inicio, data_fim, formato, prefixo="Extrato geral de"
    )

    if formato == "pdf":
        empresa = db.query(Empresa).order_by(Empresa.id).first()
        filtros = {
            "periodo": f"{data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
        }
        pdf_bytes = relatorios_pdf.gerar_extrato_geral_pdf(
            empresa, filtros, res["clientes"], res["totais"], user,
        )
        return Response(
            pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nome}"'},
        )

    dados = [
        {
            "Cliente": c["nome"],
            "NUIT": c["nuit"],
            "Saldo Inicial": f"{c['saldo_inicial']:.2f}",
            "Total Debito": f"{c['total_debito']:.2f}",
            "Total Credito": f"{c['total_credito']:.2f}",
            "Saldo Final": f"{c['saldo_final']:.2f}",
        }
        for c in res["clientes"]
    ]
    headers = ["Cliente", "NUIT", "Saldo Inicial", "Total Debito", "Total Credito", "Saldo Final"]
    titulo = relatorios.nome_extrato(
        tipo_nome, data_inicio, data_fim, "", prefixo="Extrato geral de"
    )
    return _gerar_ficheiro(dados, headers, titulo, formato, nome.rsplit(".", 1)[0])