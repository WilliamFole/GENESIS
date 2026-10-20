from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.artigo import Artigo
from app.models.unidade import Unidade
from app.models.utilizador import Perfil, Utilizador
from app.schemas.unidade import UnidadeCreate, UnidadeRead, UnidadeUpdate
from app.services import auditoria

router = APIRouter(prefix="/api/unidades", tags=["configuracao"])

_admin = require_perfis(Perfil.ADMINISTRADOR)


def _obter_ou_404(db: Session, unidade_id: int) -> Unidade:
    u = db.get(Unidade, unidade_id)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade nao encontrada")
    return u


@router.get("", response_model=list[UnidadeRead])
def listar(
    apenas_ativos: bool = False,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    query = db.query(Unidade)
    if apenas_ativos:
        query = query.filter(Unidade.ativo.is_(True))
    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(
            or_(Unidade.codigo.ilike(termo), Unidade.nome.ilike(termo))
        )
    return query.order_by(Unidade.codigo).all()


@router.post("", response_model=UnidadeRead, status_code=201)
def criar(
    payload: UnidadeCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    codigo = payload.codigo.upper().strip()
    if db.query(Unidade).filter(Unidade.codigo == codigo).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo ja existe")

    dados = payload.model_dump()
    dados["codigo"] = codigo
    u = Unidade(**dados)
    db.add(u)
    db.commit()
    db.refresh(u)

    auditoria.registar(
        db, operacao="criar_unidade", utilizador=admin,
        entidade="unidade", entidade_id=u.id,
        ip=request.client.host if request.client else None,
    )
    return u


@router.patch("/{unidade_id}", response_model=UnidadeRead)
def atualizar(
    unidade_id: int,
    payload: UnidadeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    u = _obter_ou_404(db, unidade_id)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(u, campo, valor)
    db.commit()
    db.refresh(u)

    auditoria.registar(
        db, operacao="atualizar_unidade", utilizador=admin,
        entidade="unidade", entidade_id=u.id,
        ip=request.client.host if request.client else None,
    )
    return u


@router.delete("/{unidade_id}", status_code=204)
def remover(
    unidade_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    u = _obter_ou_404(db, unidade_id)

    if db.query(Artigo).filter(Artigo.unidade_id == u.id).first():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Unidade em uso por artigos. Deve ser inativada, nao eliminada.",
        )

    db.delete(u)
    db.commit()

    auditoria.registar(
        db, operacao="remover_unidade", utilizador=admin,
        entidade="unidade", entidade_id=unidade_id,
        ip=request.client.host if request.client else None,
    )