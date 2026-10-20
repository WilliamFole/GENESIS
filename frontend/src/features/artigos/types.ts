export type Unidade = {
  id: number
  codigo: string
  nome: string
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export type Imposto = {
  id: number
  codigo: string
  descricao: string
  tipo: 'iva' | 'isento'
  percentagem: string
  motivo_isencao: string | null
  vigencia_inicio: string
  vigencia_fim: string | null
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export type Artigo = {
  id: number
  codigo: string
  descricao: string
  unidade_id: number
  imposto_id: number
  preco_unitario: string
  ativo: boolean
  criado_em: string
  atualizado_em: string
}