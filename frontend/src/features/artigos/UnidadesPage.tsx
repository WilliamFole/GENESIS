import { FormEvent, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { Unidade } from './types'

type FormState = { codigo: string; nome: string }
const VAZIO: FormState = { codigo: '', nome: '' }

export function UnidadesPage() {
  const [lista, setLista] = useState<Unidade[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [busca, setBusca] = useState('')
  const [soAtivos, setSoAtivos] = useState(false)
  const [aberto, setAberto] = useState(false)
  const [editar, setEditar] = useState<Unidade | null>(null)

  async function carregar() {
    try {
      const params = new URLSearchParams()
      if (busca.trim()) params.set('q', busca.trim())
      if (soAtivos) params.set('apenas_ativos', 'true')
      const qs = params.toString()
      const url = qs ? `/api/unidades?${qs}` : '/api/unidades'
      setLista(await api<Unidade[]>(url))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    const t = setTimeout(carregar, 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busca, soAtivos])

  async function alternarAtivo(u: Unidade) {
    try {
      await api(`/api/unidades/${u.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ativo: !u.ativo }),
      })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function remover(u: Unidade) {
    if (!confirm(`Apagar a unidade "${u.codigo}"?`)) return
    try {
      await api(`/api/unidades/${u.id}`, { method: 'DELETE' })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3 flex-1 max-w-xl">
          <input
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            placeholder="Buscar por código ou nome"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
          <label className="flex items-center gap-2 text-sm text-slate-700 whitespace-nowrap">
            <input
              type="checkbox"
              checked={soAtivos}
              onChange={(e) => setSoAtivos(e.target.checked)}
            />
            Só ativos
          </label>
        </div>
        <button
          onClick={() => {
            setEditar(null)
            setAberto(true)
          }}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Nova unidade
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Código</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="px-3 py-2">{u.codigo}</td>
                <td className="px-3 py-2">{u.nome}</td>
                <td className="px-3 py-2">
                  {u.ativo ? 'Ativa' : <span className="text-amber-700">Inativa</span>}
                </td>
                <td className="px-3 py-2 text-right space-x-3 whitespace-nowrap">
                  <button
                    onClick={() => {
                      setEditar(u)
                      setAberto(true)
                    }}
                    className="text-xs text-slate-700 hover:underline"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => alternarAtivo(u)}
                    className="text-xs text-amber-700 hover:underline"
                  >
                    {u.ativo ? 'Inativar' : 'Reativar'}
                  </button>
                  <button
                    onClick={() => remover(u)}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Apagar
                  </button>
                </td>
              </tr>
            ))}
            {lista.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-4 text-center text-slate-500">
                  Sem unidades.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {aberto && (
        <UnidadeForm
          inicial={
            editar
              ? { codigo: editar.codigo, nome: editar.nome }
              : VAZIO
          }
          edicao={editar}
          onClose={() => setAberto(false)}
          onGravado={async () => {
            setAberto(false)
            await carregar()
          }}
        />
      )}
    </div>
  )
}

function UnidadeForm({
  inicial,
  edicao,
  onClose,
  onGravado,
}: {
  inicial: FormState
  edicao: Unidade | null
  onClose: () => void
  onGravado: () => void
}) {
  const [form, setForm] = useState<FormState>(inicial)
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      if (edicao) {
        await api(`/api/unidades/${edicao.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ nome: form.nome }),
        })
      } else {
        await api('/api/unidades', {
          method: 'POST',
          body: JSON.stringify({
            codigo: form.codigo.toUpperCase(),
            nome: form.nome,
          }),
        })
      }
      onGravado()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setAEnviar(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <form
        onSubmit={onSubmit}
        className="bg-white p-6 rounded shadow w-full max-w-md space-y-3"
      >
        <h2 className="text-lg font-semibold">
          {edicao ? 'Editar unidade' : 'Nova unidade'}
        </h2>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Código *</span>
          <input
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm disabled:bg-slate-100"
            value={form.codigo}
            onChange={(e) =>
              setForm({ ...form, codigo: e.target.value.toUpperCase() })
            }
            required
            maxLength={20}
            disabled={!!edicao}
          />
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Nome *</span>
          <input
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            value={form.nome}
            onChange={(e) => setForm({ ...form, nome: e.target.value })}
            required
          />
        </label>

        {erro && <div className="text-sm text-red-600">{erro}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-slate-600"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={aEnviar}
            className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
          >
            {aEnviar ? 'A guardar…' : 'Guardar'}
          </button>
        </div>
      </form>
    </div>
  )
}