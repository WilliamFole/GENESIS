import { FormEvent, useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import type { Artigo, Imposto, Unidade } from './types'

type FormState = {
  codigo: string
  descricao: string
  unidade_id: string
  imposto_id: string
  preco_unitario: string
  ativo: boolean
}

const VAZIO: FormState = {
  codigo: '',
  descricao: '',
  unidade_id: '',
  imposto_id: '',
  preco_unitario: '',
  ativo: true,
}

function formataPreco(v: string): string {
  const n = Number(v)
  if (Number.isNaN(n)) return v
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function ArtigosPage() {
  const [lista, setLista] = useState<Artigo[]>([])
  const [unidades, setUnidades] = useState<Unidade[]>([])
  const [impostos, setImpostos] = useState<Imposto[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [busca, setBusca] = useState('')
  const [soAtivos, setSoAtivos] = useState(false)
  const [aberto, setAberto] = useState(false)
  const [editar, setEditar] = useState<Artigo | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const [us, is] = await Promise.all([
          api<Unidade[]>('/api/unidades?apenas_ativos=true'),
          api<Imposto[]>('/api/impostos?apenas_ativos=true'),
        ])
        setUnidades(us)
        setImpostos(is)
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    })()
  }, [])

  async function carregar() {
    try {
      const params = new URLSearchParams()
      if (busca.trim()) params.set('q', busca.trim())
      if (soAtivos) params.set('apenas_ativos', 'true')
      const qs = params.toString()
      const url = qs ? `/api/artigos?${qs}` : '/api/artigos'
      setLista(await api<Artigo[]>(url))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    const t = setTimeout(carregar, 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busca, soAtivos])

  const mapaUnidades = useMemo(
    () => Object.fromEntries(unidades.map((u) => [u.id, u])),
    [unidades],
  )
  const mapaImpostos = useMemo(
    () => Object.fromEntries(impostos.map((i) => [i.id, i])),
    [impostos],
  )

  async function alternarAtivo(a: Artigo) {
    try {
      await api(`/api/artigos/${a.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ativo: !a.ativo }),
      })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function remover(a: Artigo) {
    if (!confirm(`Apagar o artigo "${a.codigo}"?`)) return
    try {
      await api(`/api/artigos/${a.id}`, { method: 'DELETE' })
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
            placeholder="Buscar por código ou descrição"
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
          Novo artigo
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Código</th>
              <th className="px-3 py-2">Descrição</th>
              <th className="px-3 py-2">Unidade</th>
              <th className="px-3 py-2">Imposto</th>
              <th className="px-3 py-2 text-right">Preço c/ IVA</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((a) => {
              const u = mapaUnidades[a.unidade_id]
              const i = mapaImpostos[a.imposto_id]
              return (
                <tr key={a.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{a.codigo}</td>
                  <td className="px-3 py-2">{a.descricao}</td>
                  <td className="px-3 py-2">{u ? u.codigo : `#${a.unidade_id}`}</td>
                  <td className="px-3 py-2">
                    {i ? `${i.codigo} (${i.percentagem}%)` : `#${a.imposto_id}`}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {formataPreco(a.preco_unitario)} MZN
                  </td>
                  <td className="px-3 py-2">
                    {a.ativo ? (
                      'Ativo'
                    ) : (
                      <span className="text-amber-700">Inativo</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right space-x-3 whitespace-nowrap">
                    <button
                      onClick={() => {
                        setEditar(a)
                        setAberto(true)
                      }}
                      className="text-xs text-slate-700 hover:underline"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => alternarAtivo(a)}
                      className="text-xs text-amber-700 hover:underline"
                    >
                      {a.ativo ? 'Inativar' : 'Reativar'}
                    </button>
                    <button
                      onClick={() => remover(a)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Apagar
                    </button>
                  </td>
                </tr>
              )
            })}
            {lista.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                  Sem artigos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {aberto && (
        <ArtigoForm
          inicial={
            editar
              ? {
                  codigo: editar.codigo,
                  descricao: editar.descricao,
                  unidade_id: String(editar.unidade_id),
                  imposto_id: String(editar.imposto_id),
                  preco_unitario: editar.preco_unitario,
                  ativo: editar.ativo,
                }
              : VAZIO
          }
          edicao={editar}
          unidades={unidades}
          impostos={impostos}
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

function ArtigoForm({
  inicial,
  edicao,
  unidades,
  impostos,
  onClose,
  onGravado,
}: {
  inicial: FormState
  edicao: Artigo | null
  unidades: Unidade[]
  impostos: Imposto[]
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
      const payload = {
        descricao: form.descricao,
        unidade_id: Number(form.unidade_id),
        imposto_id: Number(form.imposto_id),
        preco_unitario: form.preco_unitario,
        ativo: form.ativo,
      }
      
      if (edicao) {
        await api(`/api/artigos/${edicao.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
      } else {
        // Envia o código como null se estiver vazio, para o backend gerar
        await api('/api/artigos', {
          method: 'POST',
          body: JSON.stringify({
            ...payload,
            codigo: form.codigo.trim() ? form.codigo.trim() : null,
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
        className="bg-white p-6 rounded shadow w-full max-w-md space-y-3 max-h-[90vh] overflow-auto"
      >
        <h2 className="text-lg font-semibold">
          {edicao ? 'Editar artigo' : 'Novo artigo'}
        </h2>

        <label className="block">
          <span className="block text-sm font-medium mb-1">
            Código (opcional)
          </span>
          <input
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm disabled:bg-slate-100"
            value={form.codigo}
            onChange={(e) => setForm({ ...form, codigo: e.target.value })}
            maxLength={40}
            disabled={!!edicao}
            placeholder="Opcional.."
          />
          <span className="text-xs text-slate-500">
            ...
          </span>
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Descrição *</span>
          <input
            className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
            value={form.descricao}
            onChange={(e) => setForm({ ...form, descricao: e.target.value })}
            required
          />
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="block text-sm font-medium mb-1">Unidade *</span>
            <select
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
              value={form.unidade_id}
              onChange={(e) => setForm({ ...form, unidade_id: e.target.value })}
              required
            >
              <option value="">Selecione...</option>
              {unidades.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.codigo} — {u.nome}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="block text-sm font-medium mb-1">Imposto *</span>
            <select
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
              value={form.imposto_id}
              onChange={(e) => setForm({ ...form, imposto_id: e.target.value })}
              required
            >
              <option value="">Selecione...</option>
              {impostos.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.codigo} ({i.percentagem}%)
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block">
          <span className="block text-sm font-medium mb-1">
            Preço unitário (com IVA) *
          </span>
          <div className="flex items-center gap-2">
            <input
              type="number"
              step="0.01"
              min="0"
              className="w-full border border-slate-300 rounded px-3 py-2 text-sm"
              value={form.preco_unitario}
              onChange={(e) =>
                setForm({ ...form, preco_unitario: e.target.value })
              }
              required
            />
            <span className="text-sm text-slate-600">MZN</span>
          </div>
          <span className="text-xs text-slate-500">
            O valor que o cliente paga. O sistema separa a base tributável e o IVA
            na fatura.
          </span>
        </label>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.ativo}
            onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
          />
          Ativo
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