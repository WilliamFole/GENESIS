from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.documento import (
    Documento, EstadoDocumento, LinhaDocumento, TipoDocumentoFiscal,
)
from app.models.moeda import Moeda
from app.models.pagamento import Pagamento
from app.models.recibo_fatura import ReciboFatura
from app.models.serie import Serie
from app.models.utilizador import Perfil, Utilizador
from app.schemas.documento import DocumentoRead
from app.schemas.recibo import ReciboCreate
from app.services import auditoria

router = APIRouter(prefix="/api/recibos", tags=["recibos"])

_pode_receber = require_perfis(Perfil.ADMINISTRADOR, Perfil.FATURACAO)


@router.get("", response_model=list[DocumentoRead])
def listar(
    cliente_id: int | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    q = db.query(Documento).filter(Documento.tipo_documento == TipoDocumentoFiscal.RC)
    if cliente_id:
        q = q.filter(Documento.cliente_id == cliente_id)
    return q.order_by(Documento.id.desc()).all()


@router.post("", response_model=DocumentoRead, status_code=201)
def criar(
    payload: ReciboCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_receber),
):
    serie = db.get(Serie, payload.serie_id)
    if not serie or not serie.ativo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Serie invalida ou fechada")
    if serie.tipo_documento.value != "RC":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Serie tem de ser do tipo RC")

    cliente = db.get(Cliente, payload.cliente_id)
    if not cliente:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cliente invalido")

    pagamentos = (
        db.query(Pagamento)
        .filter(Pagamento.id.in_(payload.pagamentos_ids))
        .all()
    )
    if len(pagamentos) != len(set(payload.pagamentos_ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pagamentos inexistentes")

    for p in pagamentos:
        if p.recibo_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Pagamento #{p.id} ja consolidado")
        if p.valor <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Pagamento #{p.id} e um estorno")
        doc = db.get(Documento, p.documento_id)
        if not doc or doc.cliente_id != cliente.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Pagamento #{p.id} pertence a outro cliente")

    por_fatura: dict[int, Decimal] = {}
    for p in pagamentos:
        por_fatura[p.documento_id] = por_fatura.get(p.documento_id, Decimal("0")) + Decimal(p.valor)

    moeda = db.query(Moeda).filter(Moeda.base.is_(True)).first()
    if not moeda:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Moeda base nao configurada")

    rc = Documento(
        tipo_documento=TipoDocumentoFiscal.RC,
        fiscal=True,
        serie_id=serie.id,
        numero=0,
        numero_formatado="",
        data_documento=payload.data_documento,
        moeda_id=moeda.id,
        taxa_cambio=Decimal("1"),
        cliente_id=cliente.id,
        cliente_nome=cliente.nome,
        cliente_nuit=cliente.nuit,
        cliente_morada=cliente.morada,
        estado=EstadoDocumento.RASCUNHO,
        observacoes=payload.observacoes,
        criado_por_id=user.id,
    )
    db.add(rc)
    db.flush()

    total = Decimal("0")
    for fatura_id, valor in por_fatura.items():
        fatura = db.get(Documento, fatura_id)
        if not fatura:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Fatura #{fatura_id} nao encontrada")

        # Codigo = Numero da fatura (ex: FT/2)
        linha = LinhaDocumento(
            documento_id=rc.id,
            artigo_id=None,
            codigo=fatura.numero_formatado,
            descricao=f"Liquidação da fatura {fatura.numero_formatado}",
            unidade="",
            quantidade=1,
            preco_unitario=valor,
            desconto_percentual=Decimal("0"),
            taxa_iva=Decimal("0"),
            base_tributavel=valor,
            valor_iva=Decimal("0"),
            total_linha=valor,
        )
        db.add(linha)
        db.add(ReciboFatura(recibo_id=rc.id, fatura_id=fatura.id, valor=valor))
        total += valor

    rc.subtotal = total
    rc.total_iva = Decimal("0")
    rc.total = total
    rc.desconto_global_percentual = Decimal("0")
    rc.desconto_global_valor = Decimal("0")

    for p in pagamentos:
        p.recibo_id = rc.id

    db.commit()
    db.refresh(rc)

    auditoria.registar(
        db, operacao="criar_recibo_rascunho", utilizador=user,
        entidade="documento", entidade_id=rc.id,
        detalhes=f"total={rc.total} pagamentos={len(pagamentos)}",
        ip=request.client.host if request.client else None,
    )
    return rc 