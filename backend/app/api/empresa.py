import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.core.paths import LOGOS_DIR
from app.models.empresa import Empresa
from app.models.utilizador import Perfil, Utilizador
from app.schemas.empresa import EmpresaRead, EmpresaUpsert
from app.services import auditoria

router = APIRouter(prefix="/api/empresa", tags=["configuracao"])

_admin = require_perfis(Perfil.ADMINISTRADOR)

ALLOWED_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
}
MAX_SIZE = 2 * 1024 * 1024


def _empresa_atual(db: Session) -> Empresa | None:
    return db.query(Empresa).order_by(Empresa.id).first()


@router.get("", response_model=EmpresaRead | None)
def obter(db: Session = Depends(get_db), _: Utilizador = Depends(get_current_user)):
    return _empresa_atual(db)


@router.put("", response_model=EmpresaRead)
def upsert(
    payload: EmpresaUpsert,
    request: Request,
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    atual = _empresa_atual(db)
    ip = request.client.host if request.client else None

    if atual is None:
        nova = Empresa(**payload.model_dump())
        db.add(nova)
        db.commit()
        db.refresh(nova)
        auditoria.registar(
            db, operacao="criar_empresa", utilizador=admin,
            entidade="empresa", entidade_id=nova.id, ip=ip,
        )
        return nova

    if payload.nuit != atual.nuit:
        existe = (
            db.query(Empresa)
            .filter(Empresa.nuit == payload.nuit, Empresa.id != atual.id)
            .first()
        )
        if existe:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "NUIT ja registado")

    for campo, valor in payload.model_dump().items():
        setattr(atual, campo, valor)
    db.commit()
    db.refresh(atual)

    auditoria.registar(
        db, operacao="atualizar_empresa", utilizador=admin,
        entidade="empresa", entidade_id=atual.id, ip=ip,
    )
    return atual


@router.post("/logotipo", response_model=EmpresaRead)
async def upload_logotipo(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Utilizador = Depends(_admin),
):
    empresa = _empresa_atual(db)
    if not empresa:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Configure o emitente primeiro")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Tipo nao permitido. Usar PNG, JPEG ou SVG.",
        )

    conteudo = await file.read()
    if len(conteudo) > MAX_SIZE:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Ficheiro excede 2 MB")

    extensao = ALLOWED_TYPES[file.content_type]
    nome = f"{uuid.uuid4().hex}{extensao}"
    destino = LOGOS_DIR / nome
    destino.write_bytes(conteudo)

    # Remove a logo antiga, se existir
    if empresa.logotipo_path:
        antigo = LOGOS_DIR / empresa.logotipo_path
        if antigo.exists():
            try:
                antigo.unlink()
            except OSError:
                pass

    empresa.logotipo_path = nome
    db.commit()
    db.refresh(empresa)

    auditoria.registar(
        db, operacao="upload_logotipo", utilizador=admin,
        entidade="empresa", entidade_id=empresa.id,
        detalhes=f"ficheiro={nome}",
        ip=request.client.host if request.client else None,
    )
    return empresa


@router.get("/logotipo")
def obter_logotipo(db: Session = Depends(get_db)):
    empresa = _empresa_atual(db)
    if not empresa or not empresa.logotipo_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sem logotipo")
    caminho = LOGOS_DIR / empresa.logotipo_path
    if not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ficheiro nao encontrado")
    return FileResponse(caminho)