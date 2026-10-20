from datetime import timedelta
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, utcnow, verify_password
from app.models.utilizador import Utilizador
from app.schemas.auth import Token
from app.schemas.utilizador import UtilizadorRead
from app.services import auditoria

import secrets
from app.core.paths import DATA_DIR

router = APIRouter(prefix="/api/auth", tags=["auth"])


RECOVERY_FILE = DATA_DIR / "recovery_code.txt"

# No arranque (main.py), deves chamar esta função para gerar o código inicial:
def gerar_codigo_recuperacao():
    if not RECOVERY_FILE.exists():
        codigo = secrets.token_hex(8).upper()
        RECOVERY_FILE.write_text(codigo)
        print(f"!!! CODIGO DE RECUPERACAO GERADO: {codigo} !!!")

# Adiciona isto no ficheiro auth.py:
from pydantic import BaseModel

class RecuperarSenha(BaseModel):
    codigo: str
    nova_password: str

@router.post("/recuperar-senha")
def recuperar_senha(payload: RecuperarSenha, db: Session = Depends(get_db)):
    if not RECOVERY_FILE.exists():
        raise HTTPException(500, "Sistema sem codigo de recuperacao.")
        
    codigo_real = RECOVERY_FILE.read_text().strip()
    if payload.codigo.strip().upper() != codigo_real:
        raise HTTPException(400, "Codigo de recuperacao incorreto.")
        
    admin = db.query(Utilizador).filter(Utilizador.username == "admin").first()
    if not admin:
        raise HTTPException(404, "Admin nao encontrado.")
        
    admin.password_hash = hash_password(payload.nova_password)
    admin.bloqueado_ate = None
    admin.tentativas_falhadas = 0
    db.commit()
    
    # Invalida o codigo antigo e gera um novo
    RECOVERY_FILE.unlink()
    gerar_codigo_recuperacao()
    
    return {"ok": True, "mensagem": "Senha do admin redefinida. Guarde o novo codigo de recuperacao impresso no terminal."}

@router.post("/login", response_model=Token)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    user = db.query(Utilizador).filter(Utilizador.username == form.username).first()

    if not user or not user.ativo:
        auditoria.registar(
            db, operacao="login_falha", entidade="utilizador",
            detalhes=f"username={form.username}", ip=ip,
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")

    agora = utcnow()
    if user.bloqueado_ate and user.bloqueado_ate > agora:
        auditoria.registar(db, operacao="login_bloqueado", utilizador=user, ip=ip)
        raise HTTPException(status.HTTP_423_LOCKED, "Conta temporariamente bloqueada")

    if not verify_password(form.password, user.password_hash):
        user.tentativas_falhadas += 1
        if user.tentativas_falhadas >= settings.MAX_LOGIN_ATTEMPTS:
            user.bloqueado_ate = agora + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.tentativas_falhadas = 0
        db.commit()
        auditoria.registar(db, operacao="login_falha", utilizador=user, ip=ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas")

    user.tentativas_falhadas = 0
    user.bloqueado_ate = None
    db.commit()

    token = create_access_token(
        subject=user.username,
        extra={"perfil": user.perfil.value, "uid": user.id},
    )
    auditoria.registar(db, operacao="login_sucesso", utilizador=user, ip=ip)
    return Token(access_token=token)


@router.get("/me", response_model=UtilizadorRead)
def me(user: Utilizador = Depends(get_current_user)):
    return user