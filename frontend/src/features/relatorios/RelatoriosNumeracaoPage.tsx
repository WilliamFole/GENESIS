import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { AuditoriaNumeracao } from './types'

export function RelatoriosNumeracaoPage() {
  const [linhas, setLinhas] = useState<AuditoriaNumeracao[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aCarregar, setACarregar] = useState(false)

  async function carregar() {
    setErro(null)
    setACarregar(true)
    try {
      setLinhas(await api<AuditoriaNumeracao[]>('/api/relatorios/numeracao'))
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
          Auditoria de Numeração
        </h1>
        <button
          onClick={carregar}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
        >
          {aCarregar ? 'A carregar...' : 'Atualizar'}
        </button>
      </div>

      {erro && <div className="text-sm text-red-600">{erro}</div>}

      <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Série</th>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2 text-right">Último Nº</th>
              <th className="px-3 py-2 text-right">Emitidos</th>
              <th className="px-3 py-2">Faltas (Gaps)</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((l) => (
              <tr key={l.serie} className="border-t border-slate-100">
                <td className="px-3 py-2 font-medium">{l.serie}</td>
                <td className="px-3 py-2">{l.tipo}</td>
                <td className="px-3 py-2 text-right">{l.ultimo}</td>
                <td className="px-3 py-2 text-right">{l.emitidos}</td>
                <td className="px-3 py-2">
                  {l.faltas.length === 0 ? (
                    <span className="text-green-600 font-medium">
                      ✓ Sequência completa
                    </span>
                  ) : (
                    <span className="text-red-600 font-medium">
                      {l.faltas.join(', ')}
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {linhas.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center text-slate-500">
                  Sem séries ativas.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}