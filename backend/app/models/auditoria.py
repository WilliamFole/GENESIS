from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utilizador_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operacao: Mapped[str] = mapped_column(String(64), nullable=False)
    entidade: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entidade_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detalhes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)