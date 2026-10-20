from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.empresa import RegimeIVA


class EmpresaBase(BaseModel):
    nuit: str = Field(min_length=1, max_length=20)
    designacao: str = Field(min_length=1, max_length=200)
    morada: str = Field(min_length=1, max_length=300)
    telefone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=120)
    atividade: str | None = Field(default=None, max_length=200)
    regime_iva: RegimeIVA
    logotipo_path: str | None = Field(default=None, max_length=300)
    numero_certificacao: str | None = Field(default=None, max_length=60)
    banco: str | None = Field(default=None, max_length=80)
    nib: str | None = Field(default=None, max_length=30)
    conta: str | None = Field(default=None, max_length=30)


class EmpresaUpsert(EmpresaBase):
    pass


class EmpresaRead(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criado_em: datetime
    atualizado_em: datetime