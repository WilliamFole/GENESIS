"""Avisos de configuracao insegura.

Nao altera o comportamento do sistema: so escreve avisos no arranque.
Com GENESIS_STRICT_SECURITY=1 o arranque e recusado se a SECRET_KEY for a de defeito.
(Nao se muda a SECRET_KEY automaticamente porque e dela que deriva a cifra das
chaves RSA ja guardadas na base de dados.)
"""
import os

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password

_SECRET_KEY_DEFEITO = "chave-secreta-padrao-mude-isso-em-producao-123456"
_ADMIN_PASSWORD_DEFEITO = "admin123"


def avisar_configuracao_insegura(db: Session) -> None:
    estrito = os.environ.get("GENESIS_STRICT_SECURITY") == "1"

    if settings.SECRET_KEY == _SECRET_KEY_DEFEITO:
        msg = "SECRET_KEY de defeito em uso. Define SECRET_KEY no ficheiro .env."
        if estrito:
            raise RuntimeError(msg)
        print(f"AVISO DE SEGURANCA: {msg}")

    try:
        from app.models.utilizador import Utilizador

        admin = (
            db.query(Utilizador)
            .filter(Utilizador.username == settings.INITIAL_ADMIN_USERNAME)
            .first()
        )
        if admin and verify_password(_ADMIN_PASSWORD_DEFEITO, admin.password_hash):
            print(
                "AVISO DE SEGURANCA: o administrador ainda usa a palavra-passe de "
                "defeito. Altera-a no menu Utilizadores."
            )
    except Exception:
        pass  # um aviso nunca pode impedir o arranque
