from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.core.security import utcnow
from app.models.fecho_caixa import EstadoFecho, FechoCaixa
from app.models.metodo_pagamento import MetodoPagamento
from app.models.pagamento import Pagamento
from app.models.utilizador import Perfil, Utilizador
from app.schemas.fecho_caixa import (
    FechoCaixaAnular, FechoCaixaCreate, FechoCaixaPreview, FechoCaixaRead,
)
from app.services import auditoria

router = APIRouter(prefix="/api/fechos-caixa", tags=["fechos-caixa"])

_pode_fechar = require_perfis(Perfil.ADMINISTRADOR, Perfil.FATURACAO)


def _totais_do_dia(db: Session, utilizador_id: int, dia: date) -> dict:
    q = (
        db.query(
            MetodoPagamento.codigo,
            func.coalesce(func.sum(Pagamento.valor), 0),
        )
        .join(MetodoPagamento, MetodoPagamento.id == Pagamento.metodo_pagamento_id)
        .filter(
            Pagamento.criado_por_id == utilizador_id,
            Pagamento.data_pagamento == dia,
        )
        .group_by(MetodoPagamento.codigo)
    )
    totais = {row[0].upper(): Decimal(row[1]) for row in q.all()}
    return {
        "numerario": totais.get("NUM", Decimal("0")),
        "transferencia": totais.get("TRF", Decimal("0")),
        "cartao": totais.get("CAR", Decimal("0")),
        "mpesa": totais.get("MPESA", Decimal("0")),
        "emola": totais.get("EMOLA", Decimal("0")),
        "cheque": totais.get("CHQ", Decimal("0")),
    }


@router.get("/preview", response_model=FechoCaixaPreview)
def preview(
    data: date | None = None,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(get_current_user),
):
    dia = data or date.today()
    t = _totais_do_dia(db, user.id, dia)
    total_geral = sum(t.values(), Decimal("0"))
    return FechoCaixaPreview(
        data=dia,
        total_numerario=t["numerario"],
        total_transferencia=t["transferencia"],
        total_cartao=t["cartao"],
        total_mpesa=t["mpesa"],
        total_emola=t["emola"],
        total_cheque=t["cheque"],
        total_geral=total_geral,
    )


@router.get("", response_model=list[FechoCaixaRead])
def listar(
    utilizador_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    q = db.query(FechoCaixa)
    if utilizador_id:
        q = q.filter(FechoCaixa.utilizador_id == utilizador_id)
    if data_inicio:
        q = q.filter(FechoCaixa.data >= data_inicio)
    if data_fim:
        q = q.filter(FechoCaixa.data <= data_fim)
    return q.order_by(FechoCaixa.data.desc(), FechoCaixa.id.desc()).all()


@router.post("", response_model=FechoCaixaRead, status_code=201)
def criar(
    payload: FechoCaixaCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_fechar),
):
    existente = db.query(FechoCaixa).filter(
        FechoCaixa.utilizador_id == user.id,
        FechoCaixa.data == payload.data,
        FechoCaixa.estado.in_([EstadoFecho.ABERTO, EstadoFecho.FECHADO]),
    ).first()
    if existente:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Ja existe fecho ativo para este dia",
        )

    t = _totais_do_dia(db, user.id, payload.data)
    fecho = FechoCaixa(
        utilizador_id=user.id,
        data=payload.data,
        total_numerario=t["numerario"],
        total_transferencia=t["transferencia"],
        total_cartao=t["cartao"],
        total_mpesa=t["mpesa"],
        total_emola=t["emola"],
        total_cheque=t["cheque"],
        observacoes=payload.observacoes,
        estado=EstadoFecho.ABERTO,
    )
    db.add(fecho)
    db.commit()
    db.refresh(fecho)

    auditoria.registar(
        db, operacao="criar_fecho_caixa", utilizador=user,
        entidade="fecho_caixa", entidade_id=fecho.id,
        detalhes=f"data={payload.data}",
        ip=request.client.host if request.client else None,
    )
    return fecho


@router.post("/{fecho_id}/fechar", response_model=FechoCaixaRead)
def fechar(
    fecho_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_fechar),
):
    fecho = db.get(FechoCaixa, fecho_id)
    if not fecho:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fecho nao encontrado")
    if fecho.utilizador_id != user.id and user.perfil != Perfil.ADMINISTRADOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Fecho de outro utilizador")
    if fecho.estado != EstadoFecho.ABERTO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Fecho nao esta aberto")

    fecho.estado = EstadoFecho.FECHADO
    fecho.fechado_em = utcnow()
    db.commit()
    db.refresh(fecho)

    auditoria.registar(
        db, operacao="fechar_caixa", utilizador=user,
        entidade="fecho_caixa", entidade_id=fecho.id,
        ip=request.client.host if request.client else None,
    )
    return fecho


@router.post("/{fecho_id}/anular", response_model=FechoCaixaRead)
def anular(
    fecho_id: int,
    payload: FechoCaixaAnular,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_fechar),
):
    fecho = db.get(FechoCaixa, fecho_id)
    if not fecho:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fecho nao encontrado")
    if fecho.utilizador_id != user.id and user.perfil != Perfil.ADMINISTRADOR:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Fecho de outro utilizador")
    if fecho.estado == EstadoFecho.ANULADO:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Fecho ja anulado")

    fecho.estado = EstadoFecho.ANULADO
    fecho.motivo_anulacao = payload.motivo_anulacao
    fecho.anulado_em = utcnow()
    db.commit()
    db.refresh(fecho)

    auditoria.registar(
        db, operacao="anular_fecho_caixa", utilizador=user,
        entidade="fecho_caixa", entidade_id=fecho.id,
        detalhes=payload.motivo_anulacao,
        ip=request.client.host if request.client else None,
    )
    return fecho