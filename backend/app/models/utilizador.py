import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class Perfil(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    FATURACAO = "faturacao"
    CONTABILISTA = "contabilista"
    AUDITOR = "auditor"


class Utilizador(Base):
    __tablename__ = "utilizadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    nome_completo: Mapped[str] = mapped_column(String(128), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[Perfil] = mapped_column(SAEnum(Perfil), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tentativas_falhadas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bloqueado_ate: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)