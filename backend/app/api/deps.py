from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.utilizador import Perfil, Utilizador

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Utilizador:
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    user = db.query(Utilizador).filter(Utilizador.username == sub).first()
    if not user or not user.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Utilizador inválido")
    return user


def require_perfis(*perfis: Perfil):
    def checker(user: Utilizador = Depends(get_current_user)) -> Utilizador:
        if user.perfil not in perfis:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem permissão")
        return user

    return checker