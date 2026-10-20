import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { fmtMoney, type ResumoSaldos } from './types'

export function RelatoriosSaldosPage() {
  const [saldos, setSaldos] = useState<ResumoSaldos | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [aCarregar, setACarregar] = useState(false)

  async function carregar() {
    setErro(null)
    setACarregar(true)
    try {
      setSaldos(await api<ResumoSaldos>('/api/relatorios/saldos'))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setACarregar(false)
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">
          Antiguidade de Saldos
        </h1>
        <button
          onClick={carregar}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
        >
          {aCarregar ? 'A carregar...' : 'Atualizar'}
        </button>
      </div>

      {erro && <div className="text-sm text-red-600">{erro}</div>}

      {saldos && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {Object.entries(saldos.totais).map(([faixa, valor]) => (
              <div
                key={faixa}
                className="bg-white border border-slate-200 p-4 rounded shadow-sm text-center"
              >
                <div className="text-xs text-slate-500 font-bold uppercase mb-1">
                  {faixa} dias
                </div>
                <div className="text-lg font-semibold text-slate-800">
                  {fmtMoney(valor)} MZN
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left">
                <tr>
                  <th className="px-3 py-2">Cliente</th>
                  <th className="px-3 py-2">Escalão Mais Antigo</th>
                  <th className="px-3 py-2 text-right">Dias em Atraso</th>
                  <th className="px-3 py-2 text-right">Saldo Devedor (MZN)</th>
                </tr>
              </thead>
              <tbody>
                {saldos.por_cliente.map((c) => (
                  <tr key={c.nome} className="border-t border-slate-100">
                    <td className="px-3 py-2">{c.nome}</td>
                    <td className="px-3 py-2">{c.faixa} dias</td>
                    <td className="px-3 py-2 text-right">{c.dias}</td>
                    <td className="px-3 py-2 text-right font-medium text-red-600">
                      {fmtMoney(c.saldo)}
                    </td>
                  </tr>
                ))}
                {saldos.por_cliente.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-3 py-4 text-center text-slate-500">
                      Sem saldos em dívida.
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