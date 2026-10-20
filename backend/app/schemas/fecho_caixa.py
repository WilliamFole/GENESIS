from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.fecho_caixa import EstadoFecho


class FechoCaixaCreate(BaseModel):
    data: date
    observacoes: str | None = Field(default=None, max_length=500)


class FechoCaixaAnular(BaseModel):
    motivo_anulacao: str = Field(min_length=3, max_length=300)


class FechoCaixaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    utilizador_id: int
    data: date
    total_numerario: Decimal
    total_transferencia: Decimal
    total_cartao: Decimal
    total_mpesa: Decimal
    total_emola: Decimal
    total_cheque: Decimal
    observacoes: str | None
    estado: EstadoFecho
    motivo_anulacao: str | None
    criado_em: datetime
    fechado_em: datetime | None
    anulado_em: datetime | None


class FechoCaixaPreview(BaseModel):
    data: date
    total_numerario: Decimal
    total_transferencia: Decimal
    total_cartao: Decimal
    total_mpesa: Decimal
    total_emola: Decimal
    total_cheque: Decimal
    total_geral: Decimal