import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class TipoImposto(str, enum.Enum):
    IVA = "iva"
    ISENTO = "isento"


class Imposto(Base):
    __tablename__ = "impostos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[TipoImposto] = mapped_column(SAEnum(TipoImposto), nullable=False)
    percentagem: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    motivo_isencao: Mapped[str | None] = mapped_column(String(200), nullable=True)
    vigencia_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    vigencia_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )