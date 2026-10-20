export type Pagamento = {
  id: number
  documento_id: number
  metodo_pagamento_id: number
  data_pagamento: string
  valor: string
  referencia: string | null
  observacoes: string | null
  motivo_estorno: string | null
  estorno_de_id: number | null
  recibo_id: number | null
  criado_em: string
  criado_por_id: number | null
}

export type MetodoPagamento = {
  id: number
  codigo: string
  nome: string
  ativo: boolean
}

export type DocumentoMin = {
  id: number
  numero_formatado: string
  tipo_documento: string
  data_documento: string
  cliente_nome: string
  total: string
  estado: string
}

export type Saldo = {
  documento_id: number
  numero_formatado: string
  total: string
  valor_pago: string
  saldo: string
  estado_pagamento: 'por_pagar' | 'parcial' | 'pago' | 'anulado'
}