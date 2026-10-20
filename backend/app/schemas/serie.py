from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.serie import TipoDocumento


class SerieBase(BaseModel):
    tipo_documento: TipoDocumento
    prefixo: str = Field(min_length=1, max_length=20)


class SerieCreate(SerieBase):
    pass


class SerieUpdate(BaseModel):
    ativo: bool | None = None


class SerieRead(SerieBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ultimo_numero: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime