export type EstadoFecho = 'aberto' | 'fechado' | 'anulado'

export type FechoCaixa = {
  id: number
  utilizador_id: number
  data: string
  total_numerario: string
  total_transferencia: string
  total_cartao: string
  total_mpesa: string
  total_emola: string
  total_cheque: string
  observacoes: string | null
  estado: EstadoFecho
  motivo_anulacao: string | null
  criado_em: string
  fechado_em: string | null
  anulado_em: string | null
}

export type FechoPreview = {
  data: string
  total_numerario: string
  total_transferencia: string
  total_cartao: string
  total_mpesa: string
  total_emola: string
  total_cheque: string
  total_geral: string
}