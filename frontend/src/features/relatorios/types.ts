import { getToken } from '@/lib/api'

// ============ Tipos ============

export type ResumoVendas = {
  totais: {
    bruto: string
    liquido: string
    iva: string
    documentos: number
  }
  por_cliente: Array<{
    cliente_id: number
    nome: string
    bruto: string
    liquido: string
  }>
}

export type DocumentoRelatorio = {
  id: number
  tipo: string
  numero: string
  data: string
  cliente: string
  estado: string
  total: string
}

export type AuditoriaNumeracao = {
  serie: string
  tipo: string
  ultimo: number
  emitidos: number
  faltas: number[]
}

export type SaldoCliente = {
  nome: string
  saldo: string
  faixa: string
  dias: number
}

export type ResumoSaldos = {
  totais: Record<string, string>
  por_cliente: SaldoCliente[]
}

export type MovimentoExtrato = {
  data: string
  tipo: string
  numero: string
  descricao: string
  debito: string
  credito: string
  saldo: string
}

export type ExtratoCliente = {
  cliente: {
    id: number
    numero: number | null
    numero_formatado: string
    nome: string
    nuit: string
    morada: string | null
  }
  periodo: { inicio: string; fim: string }
  saldo_inicial: string
  saldo_final: string
  movimentos: MovimentoExtrato[]
}

export type ExtratoGeralCliente = {
  periodo: { inicio: string; fim: string }
  clientes: Array<{
    cliente_id: number
    numero_formatado: string
    nome: string
    nuit: string
    saldo_inicial: string
    total_debito: string
    total_credito: string
    saldo_final: string
  }>
}
// ============ Helpers ============

export function fmtMoney(v: string | number): string {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function getDefaultDates() {
  const hoje = new Date()
  const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
  return {
    inicio: inicio.toISOString().slice(0, 10),
    fim: hoje.toISOString().slice(0, 10),
  }
}

/** Descarrega um relatório respeitando o nome do ficheiro do backend. */
export async function downloadRelatorio(
  url: string,
  fallbackFilename: string,
): Promise<void> {
  const token = getToken()
  const res = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    const txt = await res.text()
    throw new Error(txt || `HTTP ${res.status}`)
  }
  const blob = await res.blob()

  // Tenta ler o filename do header Content-Disposition
  const cd = res.headers.get('Content-Disposition') || ''
  let filename = fallbackFilename
  const m =
    /filename\*=UTF-8''([^;]+)/i.exec(cd) ||
    /filename="([^"]+)"/i.exec(cd) ||
    /filename=([^;]+)/i.exec(cd)
  if (m) filename = decodeURIComponent(m[1].trim().replace(/^"|"$/g, ''))

  const objUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(objUrl), 30000)
}


