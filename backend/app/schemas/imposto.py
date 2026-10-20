from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.imposto import TipoImposto


class ImpostoBase(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    descricao: str = Field(min_length=1, max_length=200)
    tipo: TipoImposto
    percentagem: Decimal = Field(ge=0, le=100)
    motivo_isencao: str | None = Field(default=None, max_length=200)
    vigencia_inicio: date
    vigencia_fim: date | None = None
    ativo: bool = True

    @model_validator(mode="after")
    def _validar(self):
        if self.tipo == TipoImposto.ISENTO:
            if self.percentagem != 0:
                raise ValueError("Imposto isento deve ter percentagem 0")
            if not self.motivo_isencao:
                raise ValueError("Imposto isento exige motivo de isencao")
        if self.vigencia_fim and self.vigencia_fim < self.vigencia_inicio:
            raise ValueError("vigencia_fim nao pode ser anterior a vigencia_inicio")
        return self


class ImpostoCreate(ImpostoBase):
    pass


class ImpostoUpdate(BaseModel):
    descricao: str | None = Field(default=None, min_length=1, max_length=200)
    percentagem: Decimal | None = Field(default=None, ge=0, le=100)
    motivo_isencao: str | None = Field(default=None, max_length=200)
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None
    ativo: bool | None = None


class ImpostoRead(ImpostoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criado_em: datetime
    atualizado_em: datetime