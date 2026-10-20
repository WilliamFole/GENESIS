from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.imposto import Imposto, TipoImposto
from app.models.utilizador import Perfil, Utilizador
from app.schemas.imposto import ImpostoCreate, ImpostoRead, ImpostoUpdate
from app.services import auditoria

router = APIRouter(prefix="/api/impostos", tags=["configuracao"])

_admin = require_perfis(Perfil.ADMINISTRADOR)


@router.get("", response_model=list[ImpostoRead])
def listar(
    apenas_ativos: bool = False,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    q = db.query(Imposto).order_by(Imposto.codigo)
    if apenas_ativos:
        q = q.filter(Imposto.ativo.is_(True))
    return q.all()


@router.post("", response_model=ImpostoRead, status_code=201)
def criar(
    payload: ImpostoCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    if db.query(Imposto).filter(Imposto.codigo == payload.codigo).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo ja existe")
    imp = Imposto(**payload.model_dump())
    db.add(imp)
    db.commit()
    db.refresh(imp)
    auditoria.registar(
        db, operacao="criar_imposto", utilizador=admin,
        entidade="imposto", entidade_id=imp.id,
        ip=request.client.host if request.client else None,
    )
    return imp


@router.patch("/{imposto_id}", response_model=ImpostoRead)
def atualizar(
    imposto_id: int,
    payload: ImpostoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    imp = db.get(Imposto, imposto_id)
    if not imp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imposto nao encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(imp, campo, valor)

    if imp.tipo == TipoImposto.ISENTO:
        if imp.percentagem != 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Isento deve ter percentagem 0")
        if not imp.motivo_isencao:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Isento exige motivo")
    if imp.vigencia_fim and imp.vigencia_fim < imp.vigencia_inicio:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "vigencia_fim invalida")

    db.commit()
    db.refresh(imp)
    auditoria.registar(
        db, operacao="atualizar_imposto", utilizador=admin,
        entidade="imposto", entidade_id=imp.id,
        ip=request.client.host if request.client else None,
    )
    return imp


@router.delete("/{imposto_id}", status_code=204)
def remover(
    imposto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    imp = db.get(Imposto, imposto_id)
    if not imp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imposto nao encontrado")
    db.delete(imp)
    db.commit()
    auditoria.registar(
        db, operacao="remover_imposto", utilizador=admin,
        entidade="imposto", entidade_id=imposto_id,
        ip=request.client.host if request.client else None,
    )