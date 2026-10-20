from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class Pagamento(Base):
    """
    Registo de um pagamento contra uma fatura.

    valor > 0: recebimento normal
    valor < 0: estorno de um pagamento anterior (motivo_estorno obrigatorio)

    recibo_id: preenchido quando o pagamento e incluido num Recibo (RC)
    finalizado. A partir dai, so se corrige por Nota de Credito no RC.
    """

    __tablename__ = "pagamentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), nullable=False)
    metodo_pagamento_id: Mapped[int] = mapped_column(
        ForeignKey("metodos_pagamento.id"), nullable=False
    )

    data_pagamento: Mapped[date] = mapped_column(Date, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(80), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Para estornos (valor < 0)
    motivo_estorno: Mapped[str | None] = mapped_column(String(300), nullable=True)
    estorno_de_id: Mapped[int | None] = mapped_column(
        ForeignKey("pagamentos.id"), nullable=True
    )

    # Preenchido quando o pagamento e "consolidado" num recibo finalizado
    recibo_id: Mapped[int | None] = mapped_column(
        ForeignKey("documentos.id"), nullable=True
    )

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    criado_por_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"), nullable=True)