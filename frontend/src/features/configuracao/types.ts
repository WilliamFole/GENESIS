export type RegimeIVA = 'geral' | 'simplificado' | 'isento'

export type Empresa = {
  id: number
  nuit: string
  designacao: string
  morada: string
  telefone: string | null
  email: string | null
  atividade: string | null
  regime_iva: RegimeIVA
  logotipo_path: string | null
  criado_em: string
  atualizado_em: string
}

export type TipoImposto = 'iva' | 'isento'

export type Imposto = {
  id: number
  codigo: string
  descricao: string
  tipo: TipoImposto
  percentagem: string
  motivo_isencao: string | null
  vigencia_inicio: string
  vigencia_fim: string | null
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export type Moeda = {
  id: number
  codigo: string
  nome: string
  simbolo: string | null
  base: boolean
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export type TaxaCambio = {
  id: number
  moeda_id: number
  taxa: string
  vigencia_inicio: string
  vigencia_fim: string | null
  criado_em: string
}

export type TipoDocumento =
  | 'FT' | 'VD' | 'FS' | 'NC' | 'ND' | 'RC' | 'COT' | 'PRO' | 'GR'

export type Serie = {
  id: number
  tipo_documento: TipoDocumento
  prefixo: string
  ultimo_numero: number
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export type MetodoPagamento = {
  id: number
  codigo: string
  nome: string
  ativo: boolean
  criado_em: string
  atualizado_em: string
}