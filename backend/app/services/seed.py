from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.utilizador import Perfil, Utilizador
from app.services import auditoria


def criar_admin_inicial(db: Session) -> None:
    existente = (
        db.query(Utilizador)
        .filter(Utilizador.username == settings.INITIAL_ADMIN_USERNAME)
        .first()
    )
    if existente:
        return

    admin = Utilizador(
        username=settings.INITIAL_ADMIN_USERNAME,
        nome_completo="Administrador",
        password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
        perfil=Perfil.ADMINISTRADOR,
        ativo=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    auditoria.registar(
        db,
        operacao="seed_admin_inicial",
        utilizador=admin,
        entidade="utilizador",
        entidade_id=admin.id,
        detalhes="Criação do administrador inicial a partir do .env",
    )