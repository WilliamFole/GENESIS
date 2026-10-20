from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class Moeda(Base):
    __tablename__ = "moedas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    simbolo: Mapped[str | None] = mapped_column(String(8), nullable=True)
    base: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )


class TaxaCambio(Base):
    __tablename__ = "taxas_cambio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    moeda_id: Mapped[int] = mapped_column(ForeignKey("moedas.id"), nullable=False)
    taxa: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    vigencia_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    vigencia_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)