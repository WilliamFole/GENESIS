from datetime import date

from pydantic import BaseModel, Field


class ReciboCreate(BaseModel):
    serie_id: int
    data_documento: date
    cliente_id: int
    pagamentos_ids: list[int] = Field(min_length=1)
    observacoes: str | None = Field(default=None, max_length=2000)