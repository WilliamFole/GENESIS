export type TipoDocumentoFiscal = 'FT' | 'VD'
export type EstadoDocumento = 'rascunho' | 'finalizado' | 'anulado'

export type Cliente = {
  id: number
  nuit: string
  nome: string
  morada: string
}

export type Serie = {
  id: number
  tipo_documento: string
  prefixo: string
  ultimo_numero: number
  ativo: boolean
}

export type Artigo = {
  id: number
  codigo: string
  descricao: string
  unidade_id: number
  imposto_id: number
  preco_unitario: string // string decimal, com IVA
}

export type LinhaDocumento = {
  id: number
  artigo_id: number | null
  codigo: string
  descricao: string
  unidade: string
  quantidade: string
  preco_unitario: string
  desconto_percentual: string
  taxa_iva: string
  base_tributavel: string
  valor_iva: string
  total_linha: string
}

export type Documento = {
  id: number
  tipo_documento: TipoDocumentoFiscal
  serie_id: number
  numero: number
  numero_formatado: string
  data_documento: string
  data_vencimento: string | null
  condicao_pagamento: string | null
  moeda_id: number
  taxa_cambio: string
  cliente_id: number | null
  cliente_nome: string
  cliente_nuit: string
  cliente_morada: string
  subtotal: string
  desconto_global_percentual: string
  desconto_global_valor: string
  total_iva: string
  total: string
  estado: EstadoDocumento
  banco: string | null
  nib: string | null
  conta: string | null
  observacoes: string | null
  hash: string | null
  assinatura: string | null
  documento_origem_id: number | null
  motivo_anulacao: string | null
  criado_em: string
  finalizado_em: string | null
  anulado_em: string | null
  linhas: LinhaDocumento[]
}