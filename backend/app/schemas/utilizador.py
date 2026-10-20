from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.utilizador import Perfil

class UtilizadorCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    nome_completo: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=4)
    perfil: Perfil
    ativo: bool = True

class UtilizadorUpdate(BaseModel):
    nome_completo: str | None = Field(default=None, min_length=1, max_length=128)
    password: str | None = Field(default=None, min_length=4)
    perfil: Perfil | None = None
    ativo: bool | None = None

class UtilizadorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    nome_completo: str
    perfil: Perfil
    ativo: bool
    criado_em: datetime