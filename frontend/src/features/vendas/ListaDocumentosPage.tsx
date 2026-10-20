import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, getToken } from '@/lib/api'
import type { Documento } from './types'

function formatMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const badgeEstado: Record<string, string> = {
  rascunho: 'bg-slate-100 text-slate-700',
  finalizado: 'bg-green-100 text-green-800',
  anulado: 'bg-red-100 text-red-800',
}

export function ListaDocumentosPage({
  titulo,
  tipos,
  linkNovo,
}: {
  titulo: string
  tipos: string[]
  linkNovo: string
}) {
  const [docs, setDocs] = useState<Documento[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const navigate = useNavigate()

  async function carregar() {
    try {
      const dados = await api<Documento[]>('/api/documentos')
      setDocs(dados.filter((d) => tipos.includes(d.tipo_documento)))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao carregar')
    }
  }

  useEffect(() => {
    carregar()
  }, [tipos])

  async function imprimirPDF(id: number) {
    try {
      const token = getToken()
      const res = await fetch(`/api/documentos/${id}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error('Erro ao gerar PDF')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function eliminar(id: number) {
    if (!confirm('Tem a certeza que deseja eliminar este rascunho?')) return
    try {
      await api(`/api/documentos/${id}`, { method: 'DELETE' })
      await carregar()
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Erro ao eliminar')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">{titulo}</h1>
        <Link
          to={linkNovo}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Criar Novo
        </Link>
      </div>

      {erro && <div className="text-sm text-red-600">{erro}</div>}

      <div className="bg-white border border-slate-200 rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">Nº</th>
              <th className="px-3 py-2">Data</th>
              <th className="px-3 py-2">Cliente</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2 text-right">Total</th>
              <th className="px-3 py-2 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id} className="border-t border-slate-100">
                <td className="px-3 py-2">{d.tipo_documento}</td>
                <td className="px-3 py-2 font-medium">
                  {d.numero_formatado || '—'}
                </td>
                <td className="px-3 py-2">{d.data_documento}</td>
                <td className="px-3 py-2">{d.cliente_nome}</td>
                <td className="px-3 py-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      badgeEstado[d.estado] || ''
                    }`}
                  >
                    {d.estado}
                  </span>
                </td>
                <td className="px-3 py-2 text-right">{formatMoney(d.total)}</td>
                <td className="px-3 py-2 text-right space-x-3 whitespace-nowrap">
                  <Link
                    to={`/vendas/faturas/${d.id}`}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Ver
                  </Link>
                  
                  <button
                    onClick={() => imprimirPDF(d.id)}
                    className="text-xs text-slate-700 hover:underline"
                  >
                    PDF
                  </button>

                  {d.estado === 'rascunho' && (
                    <button
                      onClick={() => eliminar(d.id)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Eliminar
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {docs.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                  Sem documentos emitidos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}