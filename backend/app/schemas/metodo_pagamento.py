from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetodoPagamentoBase(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    nome: str = Field(min_length=1, max_length=80)
    ativo: bool = True


class MetodoPagamentoCreate(MetodoPagamentoBase):
    pass


class MetodoPagamentoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=80)
    ativo: bool | None = None


class MetodoPagamentoRead(MetodoPagamentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criado_em: datetime
    atualizado_em: datetime