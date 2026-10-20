import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import {
  downloadRelatorio,
  fmtMoney,
  getDefaultDates,
  type ExtratoCliente,
  type ExtratoGeralCliente,
} from './types'

type ClienteMin = {
  id: number
  numero_formatado: string
  nome: string
  nuit: string
}

const inp =
  'border border-slate-300 rounded px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-slate-500'

export function RelatoriosExtratoClientePage() {
  const { inicio, fim } = getDefaultDates()
  const [clientes, setClientes] = useState<ClienteMin[]>([])
  const [clienteId, setClienteId] = useState('')
  const [dataInicio, setDataInicio] = useState(inicio)
  const [dataFim, setDataFim] = useState(fim)

  const [extrato, setExtrato] = useState<ExtratoCliente | null>(null)
  const [extratoGeral, setExtratoGeral] = useState<ExtratoGeralCliente | null>(null)
  const [modoGeral, setModoGeral] = useState(false)
  
  const [erro, setErro] = useState<string | null>(null)
  const [aCarregar, setACarregar] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const cs = await api<ClienteMin[]>('/api/clientes?apenas_ativos=true')
        setClientes(cs)
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    })()
  }, [])

  async function carregar() {
    if (!clienteId) return
    setErro(null)
    setACarregar(true)
    setModoGeral(false)
    setExtratoGeral(null)
    try {
      const ex = await api<ExtratoCliente>(
        `/api/relatorios/extrato-cliente/${clienteId}?data_inicio=${dataInicio}&data_fim=${dataFim}`,
      )
      setExtrato(ex)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setACarregar(false)
    }
  }

  async function carregarGeral() {
    setErro(null)
    setACarregar(true)
    setModoGeral(true)
    setExtrato(null)
    try {
      const ex = await api<ExtratoGeralCliente>(
        `/api/relatorios/extrato-clientes/geral?data_inicio=${dataInicio}&data_fim=${dataFim}`,
      )
      setExtratoGeral(ex)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setACarregar(false)
    }
  }

  async function exportar(formato: 'csv' | 'xlsx' | 'pdf') {
    if (modoGeral) {
      try {
        await downloadRelatorio(
          `/api/relatorios/extrato-clientes/geral/exportar/${formato}?data_inicio=${dataInicio}&data_fim=${dataFim}`,
          `extrato-geral.${formato}`,
        )
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    } else if (clienteId) {
      try {
        await downloadRelatorio(
          `/api/relatorios/extrato-cliente/${clienteId}/exportar/${formato}?data_inicio=${dataInicio}&data_fim=${dataFim}`,
          `extrato-cliente-${clienteId}.${formato}`,
        )
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    }
  }

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">
          {modoGeral ? 'Extrato Geral (Todos os Clientes)' : 'Extrato de Cliente'}
        </h1>
        {(extrato || extratoGeral) && (
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
        )}
      </div>

      <div className="bg-white border border-slate-200 p-4 rounded shadow-sm flex flex-wrap items-end gap-4">
        {!modoGeral && (
          <label className="block flex-1 min-w-[240px]">
            <span className="block text-xs font-bold text-slate-500 mb-1 uppercase">
              Cliente
            </span>
            <select
              value={clienteId}
              onChange={(e) => setClienteId(e.target.value)}
              className={`${inp} w-full`}
            >
              <option value="">— Escolher cliente —</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.numero_formatado} — {c.nome} ({c.nuit})
                </option>
              ))}
            </select>
          </label>
        )}
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
        
        {!modoGeral ? (
          <div className="flex gap-2">
            <button
              onClick={carregar}
              disabled={!clienteId || aCarregar}
              className="px-4 py-1.5 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
            >
              {aCarregar ? 'A carregar...' : 'Carregar Extrato'}
            </button>
            <button
              onClick={carregarGeral}
              disabled={aCarregar}
              className="px-4 py-1.5 bg-slate-700 text-white rounded text-sm disabled:opacity-50"
            >
              Ver Todos os Clientes
            </button>
          </div>
        ) : (
          <button
            onClick={() => setModoGeral(false)}
            className="px-4 py-1.5 bg-slate-200 text-slate-700 rounded text-sm"
          >
            Voltar ao Extrato Individual
          </button>
        )}
        
        {erro && <span className="text-red-600 text-sm ml-auto">{erro}</span>}
      </div>

      {extrato && (
        <>
          <div className="bg-white border border-slate-200 rounded shadow-sm p-4">
            <div className="flex flex-wrap gap-6 items-baseline">
              <div>
                <div className="text-xs text-slate-500 uppercase font-bold">
                  {extrato.cliente.numero_formatado}
                </div>
                <div className="text-lg font-semibold text-slate-800">
                  {extrato.cliente.nome}
                </div>
                <div className="text-sm text-slate-600">
                  NUIT {extrato.cliente.nuit}
                </div>
              </div>
              <div className="ml-auto text-right">
                <div className="text-xs text-slate-500 uppercase font-bold">
                  Saldo Inicial
                </div>
                <div className="text-lg font-medium text-slate-700">
                  {fmtMoney(extrato.saldo_inicial)} MZN
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-500 uppercase font-bold">
                  Saldo Final
                </div>
                <div
                  className={`text-lg font-bold ${
                    Number(extrato.saldo_final) > 0
                      ? 'text-red-600'
                      : Number(extrato.saldo_final) < 0
                      ? 'text-green-600'
                      : 'text-slate-800'
                  }`}
                >
                  {fmtMoney(extrato.saldo_final)} MZN
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left">
                <tr>
                  <th className="px-3 py-2">Data</th>
                  <th className="px-3 py-2">Tipo</th>
                  <th className="px-3 py-2">Nº</th>
                  <th className="px-3 py-2">Descrição</th>
                  <th className="px-3 py-2 text-right">Débito</th>
                  <th className="px-3 py-2 text-right">Crédito</th>
                  <th className="px-3 py-2 text-right">Saldo</th>
                </tr>
              </thead>
              <tbody>
                <tr className="bg-slate-50 border-t border-slate-200">
                  <td colSpan={6} className="px-3 py-2 text-slate-500 text-xs uppercase font-bold">
                    Saldo transitado
                  </td>
                  <td className="px-3 py-2 text-right font-medium">
                    {fmtMoney(extrato.saldo_inicial)}
                  </td>
                </tr>
                {extrato.movimentos.map((m, idx) => (
                  <tr key={idx} className="border-t border-slate-100">
                    <td className="px-3 py-2">{m.data}</td>
                    <td className="px-3 py-2">{m.tipo}</td>
                    <td className="px-3 py-2 font-medium">{m.numero}</td>
                    <td className="px-3 py-2">{m.descricao}</td>
                    <td className="px-3 py-2 text-right">
                      {Number(m.debito) > 0 ? fmtMoney(m.debito) : '—'}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {Number(m.credito) > 0 ? fmtMoney(m.credito) : '—'}
                    </td>
                    <td className="px-3 py-2 text-right font-medium">
                      {fmtMoney(m.saldo)}
                    </td>
                  </tr>
                ))}
                {extrato.movimentos.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                      Sem movimentos no período.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {extratoGeral && (
        <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Cliente</th>
                <th className="px-3 py-2">NUIT</th>
                <th className="px-3 py-2 text-right">Saldo Inicial</th>
                <th className="px-3 py-2 text-right">Total Débito</th>
                <th className="px-3 py-2 text-right">Total Crédito</th>
                <th className="px-3 py-2 text-right">Saldo Final</th>
              </tr>
            </thead>
            <tbody>
              {extratoGeral.clientes.map((c) => (
                <tr key={c.cliente_id} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-medium">{c.nome}</td>
                  <td className="px-3 py-2">{c.nuit}</td>
                  <td className="px-3 py-2 text-right">{fmtMoney(c.saldo_inicial)}</td>
                  <td className="px-3 py-2 text-right">{fmtMoney(c.total_debito)}</td>
                  <td className="px-3 py-2 text-right">{fmtMoney(c.total_credito)}</td>
                  <td className={`px-3 py-2 text-right font-medium ${Number(c.saldo_final) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {fmtMoney(c.saldo_final)}
                  </td>
                </tr>
              ))}
              {extratoGeral.clientes.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-3 py-4 text-center text-slate-500">
                    Sem movimentos no período.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}