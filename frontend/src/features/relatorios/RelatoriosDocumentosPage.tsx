import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import {
  downloadRelatorio,
  fmtMoney,
  getDefaultDates,
  type DocumentoRelatorio,
} from './types'

const inp =
  'border border-slate-300 rounded px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-slate-500'

export function RelatoriosDocumentosPage() {
  const { inicio, fim } = getDefaultDates()
  const [dataInicio, setDataInicio] = useState(inicio)
  const [dataFim, setDataFim] = useState(fim)
  const [tipo, setTipo] = useState('')
  const [estado, setEstado] = useState('')

  const [docs, setDocs] = useState<DocumentoRelatorio[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aCarregar, setACarregar] = useState(false)

  async function carregar() {
    setErro(null)
    setACarregar(true)
    try {
      let url = `/api/relatorios/documentos?data_inicio=${dataInicio}&data_fim=${dataFim}`
      if (tipo) url += `&tipo=${tipo}`
      if (estado) url += `&estado=${estado}`
      setDocs(await api<DocumentoRelatorio[]>(url))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setACarregar(false)
    }
  }

  useEffect(() => {
    carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataInicio, dataFim, tipo, estado])

  async function exportar(formato: 'csv' | 'xlsx' | 'pdf') {
    try {
      let url = `/api/relatorios/documentos/exportar/${formato}?data_inicio=${dataInicio}&data_fim=${dataFim}`
      if (tipo) url += `&tipo=${tipo}`
      if (estado) url += `&estado=${estado}`
      await downloadRelatorio(url, `documentos.${formato}`)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">
          Relatório de Documentos
        </h1>
        <div className="flex gap-2">
          <button
            onClick={() => exportar('xlsx')}
            className="px-3 py-1.5 bg-green-700 hover:bg-green-600 text-white rounded text-sm"
          >
            Excel
          </button>
          <button
            onClick={() => exportar('csv')}
            className="px-3 py-1.5 bg-slate-600 hover:bg-slate-500 text-white rounded text-sm"
          >
            CSV
          </button>
          <button
            onClick={() => exportar('pdf')}
            className="px-3 py-1.5 bg-red-700 hover:bg-red-600 text-white rounded text-sm"
          >
            PDF
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 p-4 rounded shadow-sm flex flex-wrap items-end gap-4">
        <label className="block">
          <span className="block text-xs font-bold text-slate-500 mb-1 uppercase">
            Data Início
          </span>
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className={inp}
          />
        </label>
        <label className="block">
          <span className="block text-xs font-bold text-slate-500 mb-1 uppercase">
            Data Fim
          </span>
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className={inp}
          />
        </label>
        <label className="block">
          <span className="block text-xs font-bold text-slate-500 mb-1 uppercase">
            Tipo
          </span>
          <select value={tipo} onChange={(e) => setTipo(e.target.value)} className={inp}>
            <option value="">Todos</option>
            <option value="FT">FT — Fatura</option>
            <option value="VD">VD — Venda</option>
            <option value="FS">FS — Fatura Simplificada</option>
            <option value="NC">NC — Nota Crédito</option>
            <option value="ND">ND — Nota Débito</option>
            <option value="RC">RC — Recibo</option>
          </select>
        </label>
        <label className="block">
          <span className="block text-xs font-bold text-slate-500 mb-1 uppercase">
            Estado
          </span>
          <select
            value={estado}
            onChange={(e) => setEstado(e.target.value)}
            className={inp}
          >
            <option value="">Todos</option>
            <option value="finalizado">Finalizado</option>
            <option value="anulado">Anulado</option>
            <option value="rascunho">Rascunho</option>
          </select>
        </label>
        <button
          onClick={carregar}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
        >
          {aCarregar ? 'A carregar...' : 'Atualizar'}
        </button>
        {erro && <span className="text-red-600 text-sm ml-auto">{erro}</span>}
      </div>

      <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">Nº</th>
              <th className="px-3 py-2">Data</th>
              <th className="px-3 py-2">Cliente</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id} className="border-t border-slate-100">
                <td className="px-3 py-2">{d.tipo}</td>
                <td className="px-3 py-2 font-medium">{d.numero}</td>
                <td className="px-3 py-2">{d.data}</td>
                <td className="px-3 py-2">{d.cliente}</td>
                <td className="px-3 py-2 capitalize">{d.estado}</td>
                <td className="px-3 py-2 text-right">{fmtMoney(d.total)}</td>
              </tr>
            ))}
            {docs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-center text-slate-500">
                  Sem documentos no período.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}