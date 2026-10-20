import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

type Auditoria = {
  id: number
  operacao: string
  utilizador_id: number | null
  utilizador_nome: string | null
  entidade: string | null
  entidade_id: number | null
  detalhes: string | null
  ip: string | null
  criado_em: string
}

function fmtDataHora(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString('pt-MZ', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const inp = 'border border-slate-300 rounded px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-1 focus:ring-slate-500'

export function AuditoriaPage() {
  const [logs, setLogs] = useState<Auditoria[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aCarregar, setACarregar] = useState(false)

  // Filtros
  const [pesquisa, setPesquisa] = useState('')
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')

  async function carregar() {
    setErro(null)
    setACarregar(true)
    try {
      const params = new URLSearchParams()
      if (pesquisa) params.set('pesquisa', pesquisa)
      if (dataInicio) params.set('data_inicio', dataInicio)
      if (dataFim) params.set('data_fim', dataFim)

      const url = `/api/auditoria?${params.toString()}`
      setLogs(await api<Auditoria[]>(url))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setACarregar(false)
    }
  }

  useEffect(() => {
    const t = setTimeout(carregar, 300)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pesquisa, dataInicio, dataFim])

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">
          Auditoria e Registo
        </h1>
        <button
          onClick={carregar}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
        >
          {aCarregar ? 'A carregar...' : 'Atualizar'}
        </button>
      </div>

      <div className="bg-white border border-slate-200 p-4 rounded shadow-sm flex flex-wrap items-end gap-3">
        <label className="block flex-1 min-w-[200px]">
          <span className="block text-xs font-bold text-slate-500 mb-1 uppercase">
            Pesquisar
          </span>
          <input
            type="text"
            placeholder="Nome, entidade ou detalhes..."
            value={pesquisa}
            onChange={(e) => setPesquisa(e.target.value)}
            className={`${inp} w-full`}
          />
        </label>
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
      </div>

      {erro && <div className="text-sm text-red-600">{erro}</div>}

      <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Data / Hora</th>
              <th className="px-3 py-2">Utilizador</th>
              <th className="px-3 py-2">Operação</th>
              <th className="px-3 py-2">Detalhes</th>
              <th className="px-3 py-2">IP</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-3 py-2 whitespace-nowrap">{fmtDataHora(l.criado_em)}</td>
                <td className="px-3 py-2 font-medium">{l.utilizador_nome ?? 'Sistema'}</td>
                <td className="px-3 py-2">
                  <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs">
                    {l.operacao}
                  </span>
                </td>
                <td className="px-3 py-2 text-slate-600">
                  {l.detalhes ?? '—'}
                  {l.entidade && (
                    <span className="text-xs text-slate-400 ml-1">
                      ({l.entidade} #{l.entidade_id})
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-slate-500 text-xs">{l.ip ?? '—'}</td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center text-slate-500">
                  Nenhum registo encontrado para estes filtros.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}