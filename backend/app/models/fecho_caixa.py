import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class EstadoFecho(str, enum.Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"
    ANULADO = "anulado"


class FechoCaixa(Base):
    """
    Fecho de caixa de um utilizador para um dia.

    - No maximo 1 fecho ABERTO ou FECHADO por (utilizador, data).
      Fechos ANULADOS sao historicos e nao bloqueiam novo fecho.
    - Fechado e imutavel. Para corrigir, anular e criar novo.
    """

    __tablename__ = "fechos_caixa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utilizador_id: Mapped[int] = mapped_column(ForeignKey("utilizadores.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)

    total_numerario: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"), nullable=False)
    total_transferencia: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"), nullable=False)
    total_cartao: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"), nullable=False)
    total_mpesa: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"), nullable=False)
    total_emola: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"), nullable=False)
    total_cheque: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"), nullable=False)

    observacoes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    estado: Mapped[EstadoFecho] = mapped_column(
        SAEnum(EstadoFecho), default=EstadoFecho.ABERTO, nullable=False
    )
    motivo_anulacao: Mapped[str | None] = mapped_column(String(300), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    fechado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    anulado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)