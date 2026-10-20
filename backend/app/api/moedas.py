from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.moeda import Moeda, TaxaCambio
from app.models.utilizador import Perfil, Utilizador
from app.schemas.moeda import (
    MoedaCreate, MoedaRead, MoedaUpdate,
    TaxaCambioCreate, TaxaCambioRead,
)
from app.services import auditoria

router = APIRouter(prefix="/api/moedas", tags=["configuracao"])

_admin = require_perfis(Perfil.ADMINISTRADOR)


@router.get("", response_model=list[MoedaRead])
def listar(db: Session = Depends(get_db), _: Utilizador = Depends(get_current_user)):
    return db.query(Moeda).order_by(Moeda.base.desc(), Moeda.codigo).all()


@router.post("", response_model=MoedaRead, status_code=201)
def criar(
    payload: MoedaCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    codigo = payload.codigo.upper()
    if db.query(Moeda).filter(Moeda.codigo == codigo).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo ja existe")
    dados = payload.model_dump()
    dados["codigo"] = codigo
    m = Moeda(**dados, base=False)
    db.add(m)
    db.commit()
    db.refresh(m)
    auditoria.registar(
        db, operacao="criar_moeda", utilizador=admin,
        entidade="moeda", entidade_id=m.id,
        ip=request.client.host if request.client else None,
    )
    return m


@router.patch("/{moeda_id}", response_model=MoedaRead)
def atualizar(
    moeda_id: int,
    payload: MoedaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    m = db.get(Moeda, moeda_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Moeda nao encontrada")
    if m.base and payload.ativo is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Moeda base nao pode ser desativada")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    auditoria.registar(
        db, operacao="atualizar_moeda", utilizador=admin,
        entidade="moeda", entidade_id=m.id,
        ip=request.client.host if request.client else None,
    )
    return m


@router.get("/{moeda_id}/taxas", response_model=list[TaxaCambioRead])
def listar_taxas(
    moeda_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    if not db.get(Moeda, moeda_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Moeda nao encontrada")
    return (
        db.query(TaxaCambio)
        .filter(TaxaCambio.moeda_id == moeda_id)
        .order_by(TaxaCambio.vigencia_inicio.desc())
        .all()
    )


@router.post("/{moeda_id}/taxas", response_model=TaxaCambioRead, status_code=201)
def criar_taxa(
    moeda_id: int,
    payload: TaxaCambioCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    m = db.get(Moeda, moeda_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Moeda nao encontrada")
    if m.base:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Moeda base nao tem taxa")
    if payload.moeda_id != moeda_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "moeda_id inconsistente")
    if payload.vigencia_fim and payload.vigencia_fim < payload.vigencia_inicio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "vigencia_fim invalida")
    t = TaxaCambio(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    auditoria.registar(
        db, operacao="criar_taxa_cambio", utilizador=admin,
        entidade="taxa_cambio", entidade_id=t.id,
        ip=request.client.host if request.client else None,
    )
    return t


@router.delete("/taxas/{taxa_id}", status_code=204)
def remover_taxa(
    taxa_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    t = db.get(TaxaCambio, taxa_id)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Taxa nao encontrada")
    db.delete(t)
    db.commit()
    auditoria.registar(
        db, operacao="remover_taxa_cambio", utilizador=admin,
        entidade="taxa_cambio", entidade_id=taxa_id,
        ip=request.client.host if request.client else None,
    )