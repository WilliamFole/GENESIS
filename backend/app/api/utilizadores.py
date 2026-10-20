from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.core.security import hash_password
from app.models.utilizador import Perfil, Utilizador
from app.schemas.utilizador import UtilizadorCreate, UtilizadorRead, UtilizadorUpdate
from app.services import auditoria

router = APIRouter(prefix="/api/utilizadores", tags=["utilizadores"])

_admin = require_perfis(Perfil.ADMINISTRADOR)


@router.get("", response_model=list[UtilizadorRead])
def listar(
    db: Session = Depends(get_db),
    _: Utilizador = Depends(_admin),
):
    return db.query(Utilizador).order_by(Utilizador.nome_completo).all()


@router.post("", response_model=UtilizadorRead, status_code=201)
def criar(
    payload: UtilizadorCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_admin),
):
    existe = db.query(Utilizador).filter(Utilizador.username == payload.username).first()
    if existe:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username ja existe")

    novo = Utilizador(
        username=payload.username,
        nome_completo=payload.nome_completo,
        password_hash=hash_password(payload.password),
        perfil=payload.perfil,
        ativo=payload.ativo,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    auditoria.registar(
        db, operacao="criar_utilizador", utilizador=user,
        entidade="utilizador", entidade_id=novo.id,
        detalhes=f"username={novo.username}",
        ip=request.client.host if request.client else None,
    )
    return novo


@router.patch("/{utilizador_id}", response_model=UtilizadorRead)
def atualizar(
    utilizador_id: int,
    payload: UtilizadorUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_admin),
):
    alvo = db.get(Utilizador, utilizador_id)
    if not alvo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Utilizador nao encontrado")

    dados = payload.model_dump(exclude_unset=True)

    # Impedir o admin de se desativar a si proprio
    if alvo.id == user.id and dados.get("ativo") is False:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Nao pode desativar a sua propria conta.",
        )

    if "password" in dados and dados["password"]:
        alvo.password_hash = hash_password(dados["password"])
    
    if "nome_completo" in dados:
        alvo.nome_completo = dados["nome_completo"]
    if "perfil" in dados:
        alvo.perfil = dados["perfil"]
    if "ativo" in dados:
        alvo.ativo = dados["ativo"]

    db.commit()
    db.refresh(alvo)

    auditoria.registar(
        db, operacao="atualizar_utilizador", utilizador=user,
        entidade="utilizador", entidade_id=alvo.id,
        ip=request.client.host if request.client else None,
    )
    return alvo