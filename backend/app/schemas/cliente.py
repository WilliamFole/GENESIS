from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

NUIT_PATTERN = r"^\d{9}$"


class ClienteBase(BaseModel):
    nuit: str = Field(min_length=9, max_length=9, pattern=NUIT_PATTERN)
    nome: str = Field(min_length=1, max_length=200)
    morada: str = Field(min_length=1, max_length=300)
    telefone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=120)


    

class ClienteCreate(ClienteBase):
    pass
    saldo_inicial: Decimal = Field(default=Decimal("0"))
    

class ClienteUpdate(BaseModel):
    nuit: str | None = Field(default=None, min_length=9, max_length=9, pattern=NUIT_PATTERN)
    nome: str | None = Field(default=None, min_length=1, max_length=200)
    morada: str | None = Field(default=None, min_length=1, max_length=300)
    telefone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=120)
    ativo: bool | None = None
    saldo_inicial: Decimal | None = None



class ClienteRead(ClienteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ativo: bool
    consumidor_final: bool
    criado_em: datetime
    atualizado_em: datetime
    saldo_inicial: Decimal = Decimal("0")
    consumidor_final: bool = False


class MovimentoContaCorrente(BaseModel):
    data: date
    documento_tipo: str
    documento_numero: str
    descricao: str
    debito: Decimal
    credito: Decimal
    saldo: Decimal


class ContaCorrente(BaseModel):
    cliente_id: int
    cliente_nome: str
    saldo: Decimal
    movimentos: list[MovimentoContaCorrente]