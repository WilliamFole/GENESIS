from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.serie import Serie
from app.models.utilizador import Perfil, Utilizador
from app.schemas.serie import SerieCreate, SerieRead, SerieUpdate
from app.services import auditoria

router = APIRouter(prefix="/api/series", tags=["configuracao"])

_admin = require_perfis(Perfil.ADMINISTRADOR)


@router.get("", response_model=list[SerieRead])
def listar(db: Session = Depends(get_db), _: Utilizador = Depends(get_current_user)):
    return db.query(Serie).order_by(Serie.tipo_documento, Serie.prefixo).all()


@router.post("", response_model=SerieRead, status_code=201)
def criar(
    payload: SerieCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    existe = (
        db.query(Serie)
        .filter(Serie.tipo_documento == payload.tipo_documento, Serie.prefixo == payload.prefixo)
        .first()
    )
    if existe:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ja existe serie com este tipo e prefixo")
    s = Serie(**payload.model_dump(), ultimo_numero=0, ativo=True)
    db.add(s)
    db.commit()
    db.refresh(s)
    auditoria.registar(
        db, operacao="criar_serie", utilizador=admin,
        entidade="serie", entidade_id=s.id,
        ip=request.client.host if request.client else None,
    )
    return s


@router.patch("/{serie_id}", response_model=SerieRead)
def atualizar(
    serie_id: int,
    payload: SerieUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    s = db.get(Serie, serie_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serie nao encontrada")
    if payload.ativo is True and not s.ativo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Serie fechada nao pode ser reaberta")
    if payload.ativo is not None:
        s.ativo = payload.ativo
    db.commit()
    db.refresh(s)
    auditoria.registar(
        db, operacao="atualizar_serie", utilizador=admin,
        entidade="serie", entidade_id=s.id,
        ip=request.client.host if request.client else None,
    )
    return s


@router.delete("/{serie_id}", status_code=204)
def remover(
    serie_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    s = db.get(Serie, serie_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serie nao encontrada")
    if s.ultimo_numero > 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Serie com documentos emitidos nao pode ser eliminada; deve ser fechada",
        )
    db.delete(s)
    db.commit()
    auditoria.registar(
        db, operacao="remover_serie", utilizador=admin,
        entidade="serie", entidade_id=serie_id,
        ip=request.client.host if request.client else None,
    )