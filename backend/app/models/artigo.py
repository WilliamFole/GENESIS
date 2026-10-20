from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class Artigo(Base):
    __tablename__ = "artigos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)

    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"), nullable=False)
    imposto_id: Mapped[int] = mapped_column(ForeignKey("impostos.id"), nullable=False)

    # Preco com IVA incluido (o cliente paga este valor).
    # No documento (M5) a base tributavel e o IVA sao calculados assim:
    #   base = preco_com_iva / (1 + taxa/100)
    #   iva  = preco_com_iva - base
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )