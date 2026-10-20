import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class TipoDocumento(str, enum.Enum):
    FT = "FT"
    VD = "VD"
    FS = "FS"
    NC = "NC"
    ND = "ND"
    RC = "RC"
    COT = "COT"
    PRO = "PRO"
    GR = "GR"


class Serie(Base):
    __tablename__ = "series"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "prefixo", name="uq_serie_tipo_prefixo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_documento: Mapped[TipoDocumento] = mapped_column(SAEnum(TipoDocumento), nullable=False)
    prefixo: Mapped[str] = mapped_column(String(20), nullable=False)
    ultimo_numero: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )