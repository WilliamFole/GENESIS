import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class TipoExportacao(str, enum.Enum):
    EDECLARACAO = "edeclaracao"
    SAFT = "saft"
    MAPA_IVA = "mapa_iva"


class FicheiroExportado(Base):
    __tablename__ = "ficheiros_exportados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[TipoExportacao] = mapped_column(SAEnum(TipoExportacao), nullable=False)
    periodo_ano: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo_mes: Mapped[int] = mapped_column(Integer, nullable=False)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)
    caminho: Mapped[str] = mapped_column(String(300), nullable=False)
    tamanho_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_parte: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_partes: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    numero_documentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    criado_por_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"), nullable=True)