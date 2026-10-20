import { FormEvent, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Serie, TipoDocumento } from './types'

const TIPOS: TipoDocumento[] = [
  'FT', 'VD', 'FS', 'NC', 'ND', 'RC', 'COT', 'PRO', 'GR',
]

const DESCRICAO: Record<TipoDocumento, string> = {
  FT: 'Fatura',
  VD: 'Venda a dinheiro / Fatura-recibo',
  FS: 'Fatura simplificada',
  NC: 'Nota de crédito',
  ND: 'Nota de débito',
  RC: 'Recibo',
  COT: 'Cotação (não fiscal)',
  PRO: 'Proforma (não fiscal)',
  GR: 'Guia de remessa (não fiscal)',
}

export function SeriesPage() {
  const [lista, setLista] = useState<Serie[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aberto, setAberto] = useState(false)
  const [form, setForm] = useState({
    tipo_documento: 'FT' as TipoDocumento,
    prefixo: '',
  })

  async function carregar() {
    try {
      setLista(await api<Serie[]>('/api/series'))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }
  useEffect(() => {
    carregar()
  }, [])

  async function criar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    try {
      await api('/api/series', { method: 'POST', body: JSON.stringify(form) })
      setForm({ tipo_documento: 'FT', prefixo: '' })
      setAberto(false)
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function fechar(id: number) {
    if (
      !confirm(
        'Fechar esta série? Esta ação não pode ser revertida — a série nunca poderá ser reaberta.',
      )
    )
      return
    try {
      await api(`/api/series/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ativo: false }),
      })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function remover(id: number) {
    if (!confirm('Remover esta série?')) return
    try {
      await api(`/api/series/${id}`, { method: 'DELETE' })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setAberto(true)}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Nova série
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">Prefixo</th>
              <th className="px-3 py-2">Último n.º</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((s) => (
              <tr key={s.id} className="border-t border-slate-100">
                <td className="px-3 py-2">
                  {s.tipo_documento} — {DESCRICAO[s.tipo_documento]}
                </td>
                <td className="px-3 py-2">{s.prefixo}</td>
                <td className="px-3 py-2">{s.ultimo_numero}</td>
                <td className="px-3 py-2">{s.ativo ? 'Ativa' : 'Fechada'}</td>
                <td className="px-3 py-2 text-right space-x-2">
                  {s.ativo && (
                    <button
                      onClick={() => fechar(s.id)}
                      className="text-xs text-amber-700 hover:underline"
                    >
                      Fechar
                    </button>
                  )}
                  {s.ultimo_numero === 0 && (
                    <button
                      onClick={() => remover(s.id)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Remover
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {lista.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-3 py-4 text-center text-slate-500"
                >
                  Sem séries.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {aberto && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <form
            onSubmit={criar}
            className="bg-white p-6 rounded shadow w-full max-w-sm space-y-3"
          >
            <h2 className="text-lg font-semibold">Nova série</h2>
            <select
              className={inp}
              value={form.tipo_documento}
              onChange={(e) =>
                setForm({
                  ...form,
                  tipo_documento: e.target.value as TipoDocumento,
                })
              }
            >
              {TIPOS.map((t) => (
                <option key={t} value={t}>
                  {t} — {DESCRICAO[t]}
                </option>
              ))}
            </select>
            <input
              className={inp}
              placeholder="Prefixo (ex.: FT2026)"
              value={form.prefixo}
              onChange={(e) => setForm({ ...form, prefixo: e.target.value })}
              required
            />
            {erro && <div className="text-sm text-red-600">{erro}</div>}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setAberto(false)}
                className="px-3 py-1.5 text-sm text-slate-600"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
              >
                Criar
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm'