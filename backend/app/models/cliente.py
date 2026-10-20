from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from app.core.database import Base
from app.core.security import utcnow


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True, index=True)
    nuit: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    morada: Mapped[str | None] = mapped_column(String(300), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    consumidor_final: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    saldo_inicial: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0"), nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    @property
    def numero_formatado(self) -> str:
        return f"CLI{self.numero:05d}" if self.numero else "—"