from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.documento import Documento, EstadoDocumento, TipoDocumentoFiscal
from app.models.metodo_pagamento import MetodoPagamento
from app.models.pagamento import Pagamento
from app.models.utilizador import Perfil, Utilizador
from app.schemas.pagamento import (
    EstornoCreate, PagamentoCreate, PagamentoRead, SaldoDocumento,
)
from app.services import auditoria

router = APIRouter(prefix="/api/pagamentos", tags=["pagamentos"])

_pode_receber = require_perfis(Perfil.ADMINISTRADOR, Perfil.FATURACAO)

_TIPOS_PAGAVEIS = {
    TipoDocumentoFiscal.FT,
    TipoDocumentoFiscal.VD,
    TipoDocumentoFiscal.FS,
}

_METODOS_COM_REFERENCIA = {"MPESA", "EMOLA", "CHQ", "TRF"}


def _validar_documento(db: Session, doc_id: int) -> Documento:
    doc = db.get(Documento, doc_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento nao encontrado")
    if doc.estado == EstadoDocumento.ANULADO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Documento anulado")
    if doc.estado != EstadoDocumento.FINALIZADO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Documento nao finalizado")
    if doc.tipo_documento not in _TIPOS_PAGAVEIS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Tipo {doc.tipo_documento.value} nao aceita pagamento",
        )
    return doc


def _total_pago(db: Session, doc_id: int) -> Decimal:
    valor = db.query(func.coalesce(func.sum(Pagamento.valor), 0)).filter(
        Pagamento.documento_id == doc_id
    ).scalar()
    return Decimal(valor)


def _total_creditado(db: Session, doc_id: int) -> Decimal:
    """Soma das Notas de Credito finalizadas que abatem a esta fatura."""
    valor = db.query(func.coalesce(func.sum(Documento.total), 0)).filter(
        Documento.documento_origem_id == doc_id,
        Documento.tipo_documento == TipoDocumentoFiscal.NC,
        Documento.estado == EstadoDocumento.FINALIZADO,
    ).scalar()
    return Decimal(valor)


def _calcular_saldo(db: Session, doc: Documento) -> Decimal:
    """Saldo real = Total da fatura - Pagamentos recebidos - Notas de Credito."""
    pago = _total_pago(db, doc.id)
    creditado = _total_creditado(db, doc.id)
    return Decimal(doc.total) - pago - creditado


def _estado_pagamento(db: Session, doc: Documento) -> str:
    if doc.estado == EstadoDocumento.ANULADO:
        return "anulado"
    
    pago = _total_pago(db, doc.id)
    creditado = _total_creditado(db, doc.id)
    saldo = Decimal(doc.total) - pago - creditado
    
    if saldo <= 0:
        # Se o saldo for zero (ou negativo), está totalmente liquidado
        return "pago"
    
    if pago > 0 or creditado > 0:
        return "parcial"
        
    return "por_pagar"


@router.get("/saldo/{doc_id}", response_model=SaldoDocumento)
def obter_saldo(
    doc_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    doc = db.get(Documento, doc_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento nao encontrado")
    
    pago = _total_pago(db, doc.id)
    creditado = _total_creditado(db, doc.id)
    saldo = Decimal(doc.total) - pago - creditado
    
    return SaldoDocumento(
        documento_id=doc.id,
        numero_formatado=doc.numero_formatado,
        total=doc.total,
        valor_pago=pago + creditado, # Mostra a soma do que já foi "resolvido" (pagamentos + NC)
        saldo=max(saldo, Decimal("0")), # Nunca mostra saldo negativo
        estado_pagamento=_estado_pagamento(db, doc),
    )


@router.get("", response_model=list[PagamentoRead])
def listar(
    documento_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    q = db.query(Pagamento)
    if documento_id:
        q = q.filter(Pagamento.documento_id == documento_id)
    if data_inicio:
        q = q.filter(Pagamento.data_pagamento >= data_inicio)
    if data_fim:
        q = q.filter(Pagamento.data_pagamento <= data_fim)
    return q.order_by(Pagamento.data_pagamento.desc(), Pagamento.id.desc()).all()


@router.post("", response_model=PagamentoRead, status_code=201)
def criar(
    payload: PagamentoCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_receber),
):
    doc = _validar_documento(db, payload.documento_id)

    metodo = db.get(MetodoPagamento, payload.metodo_pagamento_id)
    if not metodo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Metodo invalido")
    if not metodo.ativo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Metodo inativo")

    if metodo.codigo.upper() in _METODOS_COM_REFERENCIA and not (payload.referencia or "").strip():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Metodo {metodo.codigo} exige referencia",
        )

    saldo = _calcular_saldo(db, doc)
    if Decimal(payload.valor) > saldo:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Valor excede o saldo ({saldo})",
        )

    pag = Pagamento(
        documento_id=doc.id,
        metodo_pagamento_id=metodo.id,
        data_pagamento=payload.data_pagamento,
        valor=Decimal(payload.valor),
        referencia=(payload.referencia or "").strip() or None,
        observacoes=payload.observacoes,
        criado_por_id=user.id,
    )
    db.add(pag)
    db.commit()
    db.refresh(pag)

    auditoria.registar(
        db, operacao="criar_pagamento", utilizador=user,
        entidade="pagamento", entidade_id=pag.id,
        detalhes=f"doc={doc.numero_formatado} valor={pag.valor} metodo={metodo.codigo}",
        ip=request.client.host if request.client else None,
    )
    return pag


@router.post("/{pagamento_id}/estorno", response_model=PagamentoRead, status_code=201)
def estornar(
    pagamento_id: int,
    payload: EstornoCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_receber),
):
    orig = db.get(Pagamento, pagamento_id)
    if not orig:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pagamento nao encontrado")
    if orig.valor < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao se estorna um estorno")
    if orig.recibo_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Pagamento consolidado em recibo; anule o recibo",
        )
    existente = db.query(Pagamento).filter(Pagamento.estorno_de_id == orig.id).first()
    if existente:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ja estornado")

    estorno = Pagamento(
        documento_id=orig.documento_id,
        metodo_pagamento_id=orig.metodo_pagamento_id,
        data_pagamento=date.today(),
        valor=-Decimal(orig.valor),
        referencia=None,
        observacoes=f"Estorno do pagamento #{orig.id}",
        motivo_estorno=payload.motivo_estorno,
        estorno_de_id=orig.id,
        criado_por_id=user.id,
    )
    db.add(estorno)
    db.commit()
    db.refresh(estorno)

    auditoria.registar(
        db, operacao="estornar_pagamento", utilizador=user,
        entidade="pagamento", entidade_id=estorno.id,
        detalhes=f"estorno_de={orig.id}",
        ip=request.client.host if request.client else None,
    )
    return estorno