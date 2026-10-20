export type MapaIVA = {
  periodo: { ano: number; mes: number }
  por_taxa: Array<{
    taxa: string
    liquidado: { base: string; iva: string }
    dedutivel: { base: string; iva: string }
    saldo: { base: string; iva: string }
  }>
  totais: {
    liquidado_base: string
    liquidado_iva: string
    dedutivel_base: string
    dedutivel_iva: string
    saldo_base: string
    saldo_iva: string
  }
  documentos: { liquidacao: number; deducao: number; anulados: number }
}

export type FicheiroExportado = {
  id: number
  tipo: 'edeclaracao' | 'saft' | 'mapa_iva'
  periodo_ano: number
  periodo_mes: number
  formato: string
  tamanho_bytes: number
  numero_parte: number
  total_partes: number
  numero_documentos: number
  criado_em: string
}

export type GerarResponse = {
  periodo: { ano: number; mes: number }
  formato?: string
  numero_documentos?: number
  partes?: Array<{
    id: number
    nome: string
    tamanho_bytes: number
    numero_parte: number
    total_partes: number
  }>
  ficheiro_id?: number
  nome?: string
  tamanho_bytes?: number
}