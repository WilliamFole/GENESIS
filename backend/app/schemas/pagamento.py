from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PagamentoCreate(BaseModel):
    documento_id: int
    metodo_pagamento_id: int
    data_pagamento: date
    valor: Decimal = Field(gt=0)
    referencia: str | None = Field(default=None, max_length=80)
    observacoes: str | None = Field(default=None, max_length=500)


class EstornoCreate(BaseModel):
    motivo_estorno: str = Field(min_length=3, max_length=300)


class PagamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    documento_id: int
    metodo_pagamento_id: int
    data_pagamento: date
    valor: Decimal
    referencia: str | None
    observacoes: str | None
    motivo_estorno: str | None
    estorno_de_id: int | None
    recibo_id: int | None
    criado_em: datetime
    criado_por_id: int | None


class SaldoDocumento(BaseModel):
    documento_id: int
    numero_formatado: str
    total: Decimal
    valor_pago: Decimal
    saldo: Decimal
    estado_pagamento: str  # "por_pagar" | "parcial" | "pago" | "anulado"