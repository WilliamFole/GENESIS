from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ReciboFatura(Base):
    """
    Ligacao N:N entre um recibo (documento tipo RC) e as faturas que liquida.
    """

    __tablename__ = "recibo_fatura"
    __table_args__ = (UniqueConstraint("recibo_id", "fatura_id", name="uq_recibo_fatura"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recibo_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), nullable=False)
    fatura_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)