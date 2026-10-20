from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ArtigoBase(BaseModel):
    codigo: str | None = Field(default=None, max_length=30)
    descricao: str = Field(min_length=1, max_length=200)
    unidade_id: int | None = None
    imposto_id: int
    preco_unitario: Decimal
    ativo: bool = True


class ArtigoCreate(ArtigoBase):
    pass


class ArtigoUpdate(BaseModel):
    codigo: str | None = Field(default=None, max_length=30)
    descricao: str | None = Field(default=None, min_length=1, max_length=200)
    unidade_id: int | None = None
    imposto_id: int | None = None
    preco_unitario: Decimal | None = None
    ativo: bool | None = None


class ArtigoRead(ArtigoBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    codigo: str | None = None 
    unidade_simbolo: str | None = None
    taxa_iva: Decimal | None = None
    criado_em: datetime