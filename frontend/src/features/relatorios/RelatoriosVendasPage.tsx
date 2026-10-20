import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import {
  downloadRelatorio,
  fmtMoney,
  getDefaultDates,
  type ResumoVendas,
} from './types'

const inp =
  'border border-slate-300 rounded px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-slate-500'

export function RelatoriosVendasPage() {
  const { inicio, fim } = getDefaultDates()
  const [dataInicio, setDataInicio] = useState(inicio)
  const [dataFim, setDataFim] = useState(fim)

  const [vendas, setVendas] = useState<ResumoVendas | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [aCarregar, setACarregar] = useState(false)

  async function carregar() {
    setErro(null)
    setACarregar(true)
    try {
      const v = await api<ResumoVendas>(
        `/api/relatorios/vendas?data_inicio=${dataInicio}&data_fim=${dataFim}`,
      )
      setVendas(v)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setACarregar(false)
    }
  }

  useEffect(() => {
    carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataInicio, dataFim])

  async function exportar(formato: 'csv' | 'xlsx' | 'pdf') {
    try {
      await downloadRelatorio(
        `/api/relatorios/vendas/exportar/${formato}?data_inicio=${dataInicio}&data_fim=${dataFim}`,
        `vendas.${formato}`,
      )
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">
          Relatório de Vendas
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
        <button
          onClick={carregar}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
        >
          {aCarregar ? 'A carregar...' : 'Atualizar'}
        </button>
        {erro && <span className="text-red-600 text-sm ml-auto">{erro}</span>}
      </div>

      {vendas && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card titulo="Total Bruto" valor={`${fmtMoney(vendas.totais.bruto)} MZN`} />
            <Card
              titulo="Total Líquido (c/ NC)"
              valor={`${fmtMoney(vendas.totais.liquido)} MZN`}
              destaque
            />
            <Card titulo="Total IVA" valor={`${fmtMoney(vendas.totais.iva)} MZN`} />
            <Card titulo="Nº Documentos" valor={String(vendas.totais.documentos)} />
          </div>

          <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left">
                <tr>
                  <th className="px-3 py-2">Cliente</th>
                  <th className="px-3 py-2 text-right">Total Bruto (MZN)</th>
                  <th className="px-3 py-2 text-right">Total Líquido (MZN)</th>
                </tr>
              </thead>
              <tbody>
                {vendas.por_cliente.map((c) => (
                  <tr key={c.cliente_id} className="border-t border-slate-100">
                    <td className="px-3 py-2">{c.nome}</td>
                    <td className="px-3 py-2 text-right">{fmtMoney(c.bruto)}</td>
                    <td className="px-3 py-2 text-right font-medium">
                      {fmtMoney(c.liquido)}
                    </td>
                  </tr>
                ))}
                {vendas.por_cliente.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-3 py-4 text-center text-slate-500">
                      Sem vendas no período.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

function Card({
  titulo,
  valor,
  destaque,
}: {
  titulo: string
  valor: string
  destaque?: boolean
}) {
  return (
    <div
      className={`p-4 rounded border ${
        destaque ? 'bg-blue-50 border-blue-200' : 'bg-white border-slate-200 shadow-sm'
      }`}
    >
      <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">
        {titulo}
      </div>
      <div
        className={`text-xl font-bold ${
          destaque ? 'text-blue-800' : 'text-slate-800'
        }`}
      >
        {valor}
      </div>
    </div>
  )
}