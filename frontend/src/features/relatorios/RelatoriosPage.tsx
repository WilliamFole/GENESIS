import { useEffect, useState } from 'react'
import { api, getToken } from '@/lib/api'
import type {
  AuditoriaNumeracao,
  DocumentoRelatorio,
  ResumoSaldos,
  ResumoVendas,
} from './types'

function fmtMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function getDefaultDates() {
  const hoje = new Date()
  const inicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
  return {
    inicio: inicio.toISOString().slice(0, 10),
    fim: hoje.toISOString().slice(0, 10),
  }
}

export function RelatoriosPage() {
  const { inicio, fim } = getDefaultDates()
  const [dataInicio, setDataInicio] = useState(inicio)
  const [dataFim, setDataFim] = useState(fim)

  const [vendas, setVendas] = useState<ResumoVendas | null>(null)
  const [docs, setDocs] = useState<DocumentoRelatorio[]>([])
  const [numeracao, setNumeracao] = useState<AuditoriaNumeracao[]>([])
  const [saldos, setSaldos] = useState<ResumoSaldos | null>(null)

  const [filtroTipoDoc, setFiltroTipoDoc] = useState('')
  const [filtroEstadoDoc, setFiltroEstadoDoc] = useState('')

  const [erro, setErro] = useState<string | null>(null)
  const [aCarregar, setACarregar] = useState(false)

  async function carregarTudo() {
    setErro(null)
    setACarregar(true)
    try {
      const [v, d, n, s] = await Promise.all([
        api<ResumoVendas>(`/api/relatorios/vendas?data_inicio=${dataInicio}&data_fim=${dataFim}`),
        api<DocumentoRelatorio[]>(`/api/relatorios/documentos?data_inicio=${dataInicio}&data_fim=${dataFim}&tipo=${filtroTipoDoc}&estado=${filtroEstadoDoc}`),
        api<AuditoriaNumeracao[]>('/api/relatorios/numeracao'),
        api<ResumoSaldos>('/api/relatorios/saldos'),
      ])
      setVendas(v)
      setDocs(d)
      setNumeracao(n)
      setSaldos(s)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao carregar relatórios')
    } finally {
      setACarregar(false)
    }
  }

  useEffect(() => {
    carregarTudo()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataInicio, dataFim, filtroTipoDoc, filtroEstadoDoc])

  async function exportar(tipo: 'vendas' | 'documentos', formato: 'csv' | 'xlsx' | 'pdf') {
    try {
      const token = getToken()
      let url = `/api/relatorios/${tipo}/exportar/${formato}?data_inicio=${dataInicio}&data_fim=${dataFim}`
      if (tipo === 'documentos') {
        if (filtroTipoDoc) url += `&tipo=${filtroTipoDoc}`
        if (filtroEstadoDoc) url += `&estado=${filtroEstadoDoc}`
      }

      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error('Erro ao exportar')
      
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${tipo}_${dataInicio}_${dataFim}.${formato}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(a.href), 30000)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div className="space-y-8 pb-12 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-800">Relatórios</h1>
        <button
          onClick={carregarTudo}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-sm font-medium transition-colors"
        >
          {aCarregar ? 'A atualizar...' : 'Atualizar Dados'}
        </button>
      </div>

      <div className="bg-white border border-slate-200 p-4 rounded shadow-sm flex flex-wrap items-end gap-4">
        <label className="block">
          <span className="block text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Data Início</span>
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className={inp}
          />
        </label>
        <label className="block">
          <span className="block text-xs font-bold text-slate-500 mb-1 uppercase tracking-wider">Data Fim</span>
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className={inp}
          />
        </label>
        <div className="text-sm text-slate-500 ml-auto">
          {erro && <span className="text-red-600 font-medium">{erro}</span>}
        </div>
      </div>

      {/* SECÇÃO 1: VENDAS */}
      <section className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
        <div className="bg-slate-800 px-4 py-3 flex items-center justify-between text-white">
          <h2 className="font-semibold text-lg">1. Análise de Vendas</h2>
          <div className="flex gap-2">
            <button onClick={() => exportar('vendas', 'xlsx')} className="btn-export bg-green-700 hover:bg-green-600">Excel</button>
            <button onClick={() => exportar('vendas', 'csv')} className="btn-export bg-slate-600 hover:bg-slate-500">CSV</button>
            <button onClick={() => exportar('vendas', 'pdf')} className="btn-export bg-red-700 hover:bg-red-600">PDF</button>
          </div>
        </div>
        <div className="p-4 space-y-4">
          {vendas && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card titulo="Total Bruto" valor={`${fmtMoney(vendas.totais.bruto)} MZN`} />
                <Card titulo="Total Líquido (c/ NC)" valor={`${fmtMoney(vendas.totais.liquido)} MZN`} destaque />
                <Card titulo="Total IVA" valor={`${fmtMoney(vendas.totais.iva)} MZN`} />
                <Card titulo="Nº Documentos" valor={String(vendas.totais.documentos)} />
              </div>
              <table className="w-full text-sm mt-4 border border-slate-200">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="px-3 py-2 border-b border-slate-200">Cliente</th>
                    <th className="px-3 py-2 border-b border-slate-200 text-right">Total Bruto (MZN)</th>
                    <th className="px-3 py-2 border-b border-slate-200 text-right">Total Líquido (MZN)</th>
                  </tr>
                </thead>
                <tbody>
                  {vendas.por_cliente.map((c) => (
                    <tr key={c.cliente_id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-3 py-2">{c.nome}</td>
                      <td className="px-3 py-2 text-right">{fmtMoney(c.bruto)}</td>
                      <td className="px-3 py-2 text-right font-medium">{fmtMoney(c.liquido)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </section>

      {/* SECÇÃO 2: DOCUMENTOS */}
      <section className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
        <div className="bg-slate-800 px-4 py-3 flex items-center justify-between text-white">
          <h2 className="font-semibold text-lg">2. Documentos Emitidos</h2>
          <div className="flex gap-2">
            <button onClick={() => exportar('documentos', 'xlsx')} className="btn-export bg-green-700 hover:bg-green-600">Excel</button>
            <button onClick={() => exportar('documentos', 'csv')} className="btn-export bg-slate-600 hover:bg-slate-500">CSV</button>
            <button onClick={() => exportar('documentos', 'pdf')} className="btn-export bg-red-700 hover:bg-red-600">PDF</button>
          </div>
        </div>
        <div className="p-4 space-y-4">
          <div className="flex gap-4">
            <select value={filtroTipoDoc} onChange={(e) => setFiltroTipoDoc(e.target.value)} className={inp}>
              <option value="">Todos os Tipos</option>
              <option value="FT">Fatura</option>
              <option value="VD">Venda a Dinheiro</option>
              <option value="FS">Fatura Simplificada</option>
              <option value="NC">Nota de Crédito</option>
              <option value="ND">Nota de Débito</option>
              <option value="RC">Recibo</option>
            </select>
            <select value={filtroEstadoDoc} onChange={(e) => setFiltroEstadoDoc(e.target.value)} className={inp}>
              <option value="">Todos os Estados</option>
              <option value="finalizado">Finalizado</option>
              <option value="anulado">Anulado</option>
            </select>
          </div>
          <table className="w-full text-sm border border-slate-200">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-3 py-2 border-b border-slate-200">Tipo</th>
                <th className="px-3 py-2 border-b border-slate-200">Nº</th>
                <th className="px-3 py-2 border-b border-slate-200">Data</th>
                <th className="px-3 py-2 border-b border-slate-200">Cliente</th>
                <th className="px-3 py-2 border-b border-slate-200">Estado</th>
                <th className="px-3 py-2 border-b border-slate-200 text-right">Total (MZN)</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2">{d.tipo}</td>
                  <td className="px-3 py-2 font-medium">{d.numero}</td>
                  <td className="px-3 py-2">{d.data}</td>
                  <td className="px-3 py-2">{d.cliente}</td>
                  <td className="px-3 py-2 capitalize">{d.estado}</td>
                  <td className="px-3 py-2 text-right">{fmtMoney(d.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* SECÇÃO 3: NUMERAÇÃO */}
      <section className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
        <div className="bg-slate-800 px-4 py-3 text-white">
          <h2 className="font-semibold text-lg">3. Auditoria de Numeração</h2>
        </div>
        <div className="p-4">
          <table className="w-full text-sm border border-slate-200">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-3 py-2 border-b border-slate-200">Série</th>
                <th className="px-3 py-2 border-b border-slate-200">Tipo</th>
                <th className="px-3 py-2 border-b border-slate-200 text-right">Último Nº</th>
                <th className="px-3 py-2 border-b border-slate-200 text-right">Emitidos</th>
                <th className="px-3 py-2 border-b border-slate-200">Faltas (Gaps)</th>
              </tr>
            </thead>
            <tbody>
              {numeracao.map((n) => (
                <tr key={n.serie} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium">{n.serie}</td>
                  <td className="px-3 py-2">{n.tipo}</td>
                  <td className="px-3 py-2 text-right">{n.ultimo}</td>
                  <td className="px-3 py-2 text-right">{n.emitidos}</td>
                  <td className="px-3 py-2">
                    {n.faltas.length === 0 ? (
                      <span className="text-green-600 font-medium">Sequência Perfeita</span>
                    ) : (
                      <span className="text-red-600 font-medium">{n.faltas.join(', ')}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* SECÇÃO 4: SALDOS */}
      <section className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
        <div className="bg-slate-800 px-4 py-3 text-white">
          <h2 className="font-semibold text-lg">4. Antiguidade de Saldos (Dívidas)</h2>
        </div>
        <div className="p-4 space-y-4">
          {saldos && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                {Object.entries(saldos.totais).map(([faixa, valor]) => (
                  <div key={faixa} className="bg-slate-50 border border-slate-200 p-3 rounded text-center">
                    <div className="text-xs text-slate-500 font-bold mb-1">{faixa} dias</div>
                    <div className="font-semibold text-slate-800">{fmtMoney(valor)}</div>
                  </div>
                ))}
              </div>
              <table className="w-full text-sm border border-slate-200 mt-4">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="px-3 py-2 border-b border-slate-200">Cliente</th>
                    <th className="px-3 py-2 border-b border-slate-200">Escalão Mais Antigo</th>
                    <th className="px-3 py-2 border-b border-slate-200 text-right">Dias em Atraso</th>
                    <th className="px-3 py-2 border-b border-slate-200 text-right">Saldo Devedor (MZN)</th>
                  </tr>
                </thead>
                <tbody>
                  {saldos.por_cliente.map((c) => (
                    <tr key={c.nome} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-3 py-2">{c.nome}</td>
                      <td className="px-3 py-2">{c.faixa}</td>
                      <td className="px-3 py-2 text-right">{c.dias}</td>
                      <td className="px-3 py-2 text-right font-medium text-red-600">{fmtMoney(c.saldo)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </section>
    </div>
  )
}

function Card({ titulo, valor, destaque }: { titulo: string; valor: string; destaque?: boolean }) {
  return (
    <div className={`p-4 rounded border ${destaque ? 'bg-blue-50 border-blue-200' : 'bg-white border-slate-200 shadow-sm'}`}>
      <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">{titulo}</div>
      <div className={`text-xl font-bold ${destaque ? 'text-blue-800' : 'text-slate-800'}`}>{valor}</div>
    </div>
  )
}

const inp = 'border border-slate-300 rounded px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-slate-500'