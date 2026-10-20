import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utcnow


class TipoDocumentoFiscal(str, enum.Enum):
    FT = "FT"
    VD = "VD"
    FS = "FS"
    NC = "NC"
    ND = "ND"
    RC = "RC"
    COT = "COT"
    PRO = "PRO"
    GR = "GR"


class EstadoDocumento(str, enum.Enum):
    RASCUNHO = "rascunho"
    FINALIZADO = "finalizado"
    ANULADO = "anulado"


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tipo_documento: Mapped[TipoDocumentoFiscal] = mapped_column(
        SAEnum(TipoDocumentoFiscal, native_enum=False, length=10), nullable=False
    )
    # Documentos nao fiscais (COT, PRO, GR) nao geram obrigacao fiscal,
    # nao entram na cadeia de hash e nao contam para o SAF-T.
    fiscal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    serie_id: Mapped[int] = mapped_column(ForeignKey("series.id"), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_formatado: Mapped[str] = mapped_column(String(40), nullable=False)

    data_documento: Mapped[date] = mapped_column(Date, nullable=False)
    data_vencimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    condicao_pagamento: Mapped[str | None] = mapped_column(String(80), nullable=True)

    moeda_id: Mapped[int] = mapped_column(ForeignKey("moedas.id"), nullable=False)
    taxa_cambio: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, default=Decimal("1")
    )

    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    cliente_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cliente_nuit: Mapped[str] = mapped_column(String(20), nullable=False)
    cliente_morada: Mapped[str] = mapped_column(String(300), nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    desconto_global_percentual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    desconto_global_valor: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0")
    )
    total_iva: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))

    estado: Mapped[EstadoDocumento] = mapped_column(
        SAEnum(EstadoDocumento), nullable=False, default=EstadoDocumento.RASCUNHO
    )

    banco: Mapped[str | None] = mapped_column(String(80), nullable=True)
    nib: Mapped[str | None] = mapped_column(String(30), nullable=True)
    conta: Mapped[str | None] = mapped_column(String(30), nullable=True)

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assinatura: Mapped[str | None] = mapped_column(Text, nullable=True)

    documento_origem_id: Mapped[int | None] = mapped_column(
        ForeignKey("documentos.id"), nullable=True
    )

    motivo_anulacao: Mapped[str | None] = mapped_column(String(300), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    criado_por_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"), nullable=True)
    finalizado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finalizado_por_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"), nullable=True)
    anulado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    anulado_por_id: Mapped[int | None] = mapped_column(ForeignKey("utilizadores.id"), nullable=True)

    linhas: Mapped[list["LinhaDocumento"]] = relationship(
        "LinhaDocumento",
        cascade="all, delete-orphan",
        order_by="LinhaDocumento.id",
        lazy="selectin",
    )


class LinhaDocumento(Base):
    __tablename__ = "linhas_documento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos.id"), nullable=False)

    artigo_id: Mapped[int | None] = mapped_column(ForeignKey("artigos.id"), nullable=True)

    # Em NC/ND, cada linha pode referenciar a linha correspondente do documento
    # de origem que esta a compensar.
    documento_origem_linha_id: Mapped[int | None] = mapped_column(
        ForeignKey("linhas_documento.id"), nullable=True
    )

    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), nullable=False)

    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    desconto_percentual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    taxa_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    base_tributavel: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    valor_iva: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_linha: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)