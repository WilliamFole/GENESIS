from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.documento import EstadoDocumento, TipoDocumentoFiscal


class LinhaCreate(BaseModel):
    artigo_id: int
    quantidade: int = Field(gt=0)
    desconto_percentual: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    preco_unitario: Decimal | None = Field(default=None, ge=0)
    documento_origem_linha_id: int | None = None


class LinhaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    artigo_id: int | None
    documento_origem_linha_id: int | None
    codigo: str
    descricao: str
    unidade: str
    quantidade: int
    preco_unitario: Decimal
    desconto_percentual: Decimal
    taxa_iva: Decimal
    base_tributavel: Decimal
    valor_iva: Decimal
    total_linha: Decimal


class DocumentoBase(BaseModel):
    tipo_documento: TipoDocumentoFiscal
    serie_id: int
    data_documento: date
    data_vencimento: date | None = None
    condicao_pagamento: str | None = Field(default=None, max_length=80)
    cliente_id: int | None = None
    desconto_global_percentual: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    observacoes: str | None = Field(default=None, max_length=2000)
    documento_origem_id: int | None = None


class DocumentoCreate(DocumentoBase):
    linhas: list[LinhaCreate] = Field(min_length=1)


class DocumentoUpdate(BaseModel):
    data_vencimento: date | None = None
    condicao_pagamento: str | None = Field(default=None, max_length=80)
    cliente_id: int | None = None
    desconto_global_percentual: Decimal | None = Field(default=None, ge=0, le=100)
    observacoes: str | None = Field(default=None, max_length=2000)
    linhas: list[LinhaCreate] | None = None


class DocumentoAnular(BaseModel):
    motivo_anulacao: str = Field(min_length=3, max_length=300)


class DocumentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo_documento: TipoDocumentoFiscal
    fiscal: bool
    serie_id: int
    numero: int
    numero_formatado: str
    data_documento: date
    data_vencimento: date | None
    condicao_pagamento: str | None
    moeda_id: int
    taxa_cambio: Decimal
    cliente_id: int | None
    cliente_nome: str
    cliente_nuit: str
    cliente_morada: str
    subtotal: Decimal
    desconto_global_percentual: Decimal
    desconto_global_valor: Decimal
    total_iva: Decimal
    total: Decimal
    estado: EstadoDocumento
    banco: str | None
    nib: str | None
    conta: str | None
    observacoes: str | None
    hash: str | None
    assinatura: str | None
    documento_origem_id: int | None
    motivo_anulacao: str | None
    criado_em: datetime
    finalizado_em: datetime | None
    anulado_em: datetime | None
    linhas: list[LinhaRead]