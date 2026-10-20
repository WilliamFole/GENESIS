from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.metodo_pagamento import MetodoPagamento
from app.models.utilizador import Perfil, Utilizador
from app.schemas.metodo_pagamento import (
    MetodoPagamentoCreate, MetodoPagamentoRead, MetodoPagamentoUpdate,
)
from app.services import auditoria

router = APIRouter(prefix="/api/metodos-pagamento", tags=["configuracao"])

_admin = require_perfis(Perfil.ADMINISTRADOR)


@router.get("", response_model=list[MetodoPagamentoRead])
def listar(db: Session = Depends(get_db), _: Utilizador = Depends(get_current_user)):
    return db.query(MetodoPagamento).order_by(MetodoPagamento.codigo).all()


@router.post("", response_model=MetodoPagamentoRead, status_code=201)
def criar(
    payload: MetodoPagamentoCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    codigo = payload.codigo.upper()
    if db.query(MetodoPagamento).filter(MetodoPagamento.codigo == codigo).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo ja existe")
    dados = payload.model_dump()
    dados["codigo"] = codigo
    m = MetodoPagamento(**dados)
    db.add(m)
    db.commit()
    db.refresh(m)
    auditoria.registar(
        db, operacao="criar_metodo_pagamento", utilizador=admin,
        entidade="metodo_pagamento", entidade_id=m.id,
        ip=request.client.host if request.client else None,
    )
    return m


@router.patch("/{mp_id}", response_model=MetodoPagamentoRead)
def atualizar(
    mp_id: int,
    payload: MetodoPagamentoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    m = db.get(MetodoPagamento, mp_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Metodo nao encontrado")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    auditoria.registar(
        db, operacao="atualizar_metodo_pagamento", utilizador=admin,
        entidade="metodo_pagamento", entidade_id=m.id,
        ip=request.client.host if request.client else None,
    )
    return m


@router.delete("/{mp_id}", status_code=204)
def remover(
    mp_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    m = db.get(MetodoPagamento, mp_id)
    if not m:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Metodo nao encontrado")
    db.delete(m)
    db.commit()
    auditoria.registar(
        db, operacao="remover_metodo_pagamento", utilizador=admin,
        entidade="metodo_pagamento", entidade_id=mp_id,
        ip=request.client.host if request.client else None,
    )