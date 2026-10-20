from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.artigo import Artigo
from app.models.imposto import Imposto
from app.models.utilizador import Perfil, Utilizador
from app.schemas.artigo import ArtigoCreate, ArtigoRead, ArtigoUpdate
from app.services import auditoria

router = APIRouter(prefix="/api/artigos", tags=["artigos"])

_pode_escrever = require_perfis(Perfil.ADMINISTRADOR, Perfil.FATURACAO)


def _obter_ou_404(db: Session, artigo_id: int) -> Artigo:
    a = db.get(Artigo, artigo_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artigo nao encontrado")
    return a


def _gerar_codigo(db: Session, base: str = "ART") -> str:
    # Gera algo como ART-0001
    count = db.query(func.count(Artigo.id)).scalar() or 0
    proximo = count + 1
    while True:
        codigo = f"{base}-{proximo:04d}"
        if not db.query(Artigo).filter(Artigo.codigo == codigo).first():
            return codigo
        proximo += 1


@router.get("", response_model=list[ArtigoRead])
def listar(
    q: str | None = None,
    apenas_ativos: bool = False,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    query = db.query(Artigo)
    if apenas_ativos:
        query = query.filter(Artigo.ativo.is_(True))
    if q:
        filtro = f"%{q}%"
        query = query.filter(
            (Artigo.descricao.ilike(filtro)) | (Artigo.codigo.ilike(filtro))
        )
    return query.order_by(Artigo.codigo).all()


@router.get("/{artigo_id}", response_model=ArtigoRead)
def obter(
    artigo_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    return _obter_ou_404(db, artigo_id)


@router.post("", response_model=ArtigoRead, status_code=201)
def criar(
    payload: ArtigoCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_escrever),
):
    # Valida imposto
    imp = db.get(Imposto, payload.imposto_id)
    if not imp:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Imposto invalido")

    # Se o utilizador não inseriu código, gera um.
    # Se inseriu, verifica se já existe.
    codigo_final = payload.codigo.strip() if payload.codigo else ""
    if not codigo_final:
        # Se for um serviço, podemos usar "SRV" como base. 
        # Mas para simplificar, usamos "ART" ou a base que o utilizador preferir.
        codigo_final = _gerar_codigo(db, "ART")
    else:
        existe = db.query(Artigo).filter(Artigo.codigo == codigo_final).first()
        if existe:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Ja existe um artigo com este codigo",
            )

    artigo = Artigo(
        codigo=codigo_final,
        descricao=payload.descricao,
        unidade_id=payload.unidade_id,
        imposto_id=payload.imposto_id,
        preco_unitario=payload.preco_unitario,
        ativo=payload.ativo,
    )
    db.add(artigo)
    db.commit()
    db.refresh(artigo)

    auditoria.registar(
        db, operacao="criar_artigo", utilizador=user,
        entidade="artigo", entidade_id=artigo.id,
        detalhes=f"codigo={artigo.codigo}",
        ip=request.client.host if request.client else None,
    )
    return artigo


@router.put("/{artigo_id}", response_model=ArtigoRead)
def atualizar(
    artigo_id: int,
    payload: ArtigoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_escrever),
):
    artigo = _obter_ou_404(db, artigo_id)
    dados = payload.model_dump(exclude_unset=True)

    if "codigo" in dados and dados["codigo"]:
        if dados["codigo"] != artigo.codigo:
            existe = db.query(Artigo).filter(Artigo.codigo == dados["codigo"], Artigo.id != artigo.id).first()
            if existe:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Codigo ja em uso")

    if "imposto_id" in dados:
        imp = db.get(Imposto, dados["imposto_id"])
        if not imp:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Imposto invalido")

    for k, v in dados.items():
        setattr(artigo, k, v)
    db.commit()
    db.refresh(artigo)

    auditoria.registar(
        db, operacao="atualizar_artigo", utilizador=user,
        entidade="artigo", entidade_id=artigo.id,
        ip=request.client.host if request.client else None,
    )
    return artigo


@router.delete("/{artigo_id}", status_code=204)
def eliminar(
    artigo_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(_pode_escrever),
):
    artigo = _obter_ou_404(db, artigo_id)
    db.delete(artigo)
    db.commit()
    return None