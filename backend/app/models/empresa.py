import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class RegimeIVA(str, enum.Enum):
    GERAL = "geral"
    SIMPLIFICADO = "simplificado"
    ISENTO = "isento"


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nuit: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    designacao: Mapped[str] = mapped_column(String(200), nullable=False)
    morada: Mapped[str] = mapped_column(String(300), nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    atividade: Mapped[str | None] = mapped_column(String(200), nullable=True)
    regime_iva: Mapped[RegimeIVA] = mapped_column(SAEnum(RegimeIVA), nullable=False)
    logotipo_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    numero_certificacao: Mapped[str | None] = mapped_column(String(60), nullable=True)
    banco: Mapped[str | None] = mapped_column(String(80), nullable=True)
    nib: Mapped[str | None] = mapped_column(String(30), nullable=True)
    conta: Mapped[str | None] = mapped_column(String(30), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )