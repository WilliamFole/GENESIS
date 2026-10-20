from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import utcnow


class ChaveAssinatura(Base):
    """
    Par de chaves RSA por emitente. A chave privada fica cifrada
    com SECRET_KEY (via Fernet/PBKDF2). So a chave ativa assina
    documentos novos; as revogadas continuam a permitir verificacao.
    """

    __tablename__ = "chaves_assinatura"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chave_privada_cifrada: Mapped[str] = mapped_column(Text, nullable=False)
    chave_publica_pem: Mapped[str] = mapped_column(Text, nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    motivo_revogacao: Mapped[str | None] = mapped_column(String(300), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    revogada_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)