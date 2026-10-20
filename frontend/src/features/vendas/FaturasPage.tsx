import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getToken } from '@/lib/api'
import type { Documento, EstadoDocumento } from './types'

function formatMoney(v: string) {
  const n = Number(v)
  if (Number.isNaN(n)) return v
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function stateLabel(estado: EstadoDocumento) {
  switch (estado) {
    case 'rascunho':
      return <span className="text-slate-600">Rascunho</span>
    case 'finalizado':
      return <span className="text-green-700">Finalizado</span>
    case 'anulado':
      return <span className="text-red-700">Anulado</span>
  }
}

async function verPdf(docId: number) {
  try {
    const token = getToken()
    const res = await fetch(`/api/documentos/${docId}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) {
      const txtErr = await res.text()
      throw new Error(txtErr || `HTTP ${res.status}`)
    }
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (e) {
    alert(e instanceof Error ? e.message : 'Erro ao gerar PDF')
  }
}
export function FaturasPage() {
  const navigate = useNavigate()
  const [lista, setLista] = useState<Documento[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [busca, setBusca] = useState('')
  const [apenasFinais, setApenasFinais] = useState(false)

  async function carregar() {
    try {
      const params = new URLSearchParams()
      params.set('tipo', 'FT')
      if (apenasFinais) params.set('estado', 'finalizado')
      const url = `/api/documentos?${params.toString()}`
      const dados = await api<Documento[]>(url)
      const filtrados = busca.trim()
        ? dados.filter(
            (d) =>
              d.numero_formatado.toLowerCase().includes(busca.toLowerCase()) ||
              d.cliente_nome.toLowerCase().includes(busca.toLowerCase()) ||
              d.cliente_nuit.includes(busca),
          )
        : dados
      setLista(filtrados)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    const t = setTimeout(carregar, 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busca, apenasFinais])

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3 flex-1 max-w-xl">
          <input
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            placeholder="Buscar por número, cliente ou NUIT"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
          <label className="flex items-center gap-2 text-sm text-slate-700 whitespace-nowrap">
            <input
              type="checkbox"
              checked={apenasFinais}
              onChange={(e) => setApenasFinais(e.target.checked)}
            />
            Só finalizadas
          </label>
        </div>
        <button
          onClick={() => navigate('/vendas/faturas/nova')}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Nova fatura
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Número</th>
              <th className="px-3 py-2">Data</th>
              <th className="px-3 py-2">Cliente</th>
              <th className="px-3 py-2">NUIT</th>
              <th className="px-3 py-2 text-right">Total</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((d) => (
              <tr key={d.id} className="border-t border-slate-100">
                <td className="px-3 py-2">
                  {d.estado === 'rascunho' ? <em className="text-slate-500">Rascunho</em> : d.numero_formatado}
                </td>
                <td className="px-3 py-2">{d.data_documento}</td>
                <td className="px-3 py-2">{d.cliente_nome}</td>
                <td className="px-3 py-2">{d.cliente_nuit}</td>
                <td className="px-3 py-2 text-right">{formatMoney(d.total)} MZN</td>
                <td className="px-3 py-2">{stateLabel(d.estado)}</td>
                <td className="px-3 py-2 text-right space-x-3 whitespace-nowrap">
                  {d.estado === 'rascunho' && (
                    <Link
                      to={`/vendas/faturas/${d.id}`}
                      className="text-xs text-slate-700 hover:underline"
                    >
                      Editar rascunho
                    </Link>
                  )}
                  {(d.estado === 'finalizado' || d.estado === 'anulado') && (
                    <>
                      <Link
                        to={`/vendas/faturas/${d.id}`}
                        className="text-xs text-slate-700 hover:underline"
                      >
                        Ver
                      </Link>
                      <button
                        type="button"
                        onClick={() => verPdf(d.id)}
                        className="text-xs text-slate-700 hover:underline"
                      >
                        PDF
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {lista.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                  Sem faturas.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}