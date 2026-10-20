from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditoriaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    operacao: str
    utilizador_id: int | None = None
    utilizador_nome: str | None = None
    entidade: str | None = None
    entidade_id: int | None = None
    detalhes: str | None = None
    ip: str | None = None
    criado_em: datetime