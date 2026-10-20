from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MoedaBase(BaseModel):
    codigo: str = Field(min_length=3, max_length=3)
    nome: str = Field(min_length=1, max_length=80)
    simbolo: str | None = Field(default=None, max_length=8)
    ativo: bool = True


class MoedaCreate(MoedaBase):
    pass


class MoedaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=80)
    simbolo: str | None = Field(default=None, max_length=8)
    ativo: bool | None = None


class MoedaRead(MoedaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    base: bool
    criado_em: datetime
    atualizado_em: datetime


class TaxaCambioBase(BaseModel):
    moeda_id: int
    taxa: Decimal = Field(gt=0)
    vigencia_inicio: date
    vigencia_fim: date | None = None


class TaxaCambioCreate(TaxaCambioBase):
    pass


class TaxaCambioRead(TaxaCambioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criado_em: datetime