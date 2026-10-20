import { FormEvent, ReactNode, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Imposto, TipoImposto } from './types'

type FormState = {
  codigo: string
  descricao: string
  tipo: TipoImposto
  percentagem: string
  motivo_isencao: string
  vigencia_inicio: string
  vigencia_fim: string
  ativo: boolean
}

const hoje = () => new Date().toISOString().slice(0, 10)

const VAZIO: FormState = {
  codigo: '',
  descricao: '',
  tipo: 'iva',
  percentagem: '0',
  motivo_isencao: '',
  vigencia_inicio: hoje(),
  vigencia_fim: '',
  ativo: true,
}

export function ImpostosPage() {
  const [lista, setLista] = useState<Imposto[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aberto, setAberto] = useState(false)
  const [editar, setEditar] = useState<Imposto | null>(null)

  async function carregar() {
    try {
      setLista(await api<Imposto[]>('/api/impostos'))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }
  useEffect(() => {
    carregar()
  }, [])

  async function remover(id: number) {
    if (!confirm('Remover este imposto?')) return
    try {
      await api(`/api/impostos/${id}`, { method: 'DELETE' })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          onClick={() => {
            setEditar(null)
            setAberto(true)
          }}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Novo imposto
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <Tabela
        colunas={['Código', 'Descrição', 'Tipo', '%', 'Vigência', 'Ativo', '']}
        linhas={lista.map((i) => [
          i.codigo,
          i.descricao,
          i.tipo === 'iva' ? 'IVA' : 'Isento',
          i.percentagem,
          `${i.vigencia_inicio}${i.vigencia_fim ? ' → ' + i.vigencia_fim : ''}`,
          i.ativo ? 'Sim' : 'Não',
          <div key={i.id} className="flex gap-3 justify-end">
            <button
              onClick={() => {
                setEditar(i)
                setAberto(true)
              }}
              className="text-slate-700 hover:underline text-xs"
            >
              Editar
            </button>
            <button
              onClick={() => remover(i.id)}
              className="text-red-600 hover:underline text-xs"
            >
              Remover
            </button>
          </div>,
        ])}
      />

      {aberto && (
        <ImpostoForm
          inicial={
            editar
              ? {
                  codigo: editar.codigo,
                  descricao: editar.descricao,
                  tipo: editar.tipo,
                  percentagem: editar.percentagem,
                  motivo_isencao: editar.motivo_isencao ?? '',
                  vigencia_inicio: editar.vigencia_inicio,
                  vigencia_fim: editar.vigencia_fim ?? '',
                  ativo: editar.ativo,
                }
              : VAZIO
          }
          edicaoId={editar?.id ?? null}
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

function ImpostoForm({
  inicial,
  edicaoId,
  onClose,
  onGravado,
}: {
  inicial: FormState
  edicaoId: number | null
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
      const base = {
        descricao: form.descricao,
        tipo: form.tipo,
        percentagem: form.percentagem,
        motivo_isencao:
          form.tipo === 'isento' ? form.motivo_isencao || null : null,
        vigencia_inicio: form.vigencia_inicio,
        vigencia_fim: form.vigencia_fim || null,
        ativo: form.ativo,
      }
      if (edicaoId) {
        await api(`/api/impostos/${edicaoId}`, {
          method: 'PATCH',
          body: JSON.stringify(base),
        })
      } else {
        await api('/api/impostos', {
          method: 'POST',
          body: JSON.stringify({ ...base, codigo: form.codigo }),
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
          {edicaoId ? 'Editar imposto' : 'Novo imposto'}
        </h2>

        {!edicaoId && (
          <input
            className={inp}
            placeholder="Código"
            value={form.codigo}
            onChange={(e) => setForm({ ...form, codigo: e.target.value })}
            required
          />
        )}
        <input
          className={inp}
          placeholder="Descrição"
          value={form.descricao}
          onChange={(e) => setForm({ ...form, descricao: e.target.value })}
          required
        />

        <select
          className={inp}
          value={form.tipo}
          onChange={(e) =>
            setForm({ ...form, tipo: e.target.value as TipoImposto })
          }
          disabled={!!edicaoId}
        >
          <option value="iva">IVA</option>
          <option value="isento">Isento</option>
        </select>

        <input
          className={inp}
          placeholder="Percentagem"
          type="number"
          step="0.01"
          value={form.percentagem}
          onChange={(e) => setForm({ ...form, percentagem: e.target.value })}
          required
        />

        {form.tipo === 'isento' && (
          <input
            className={inp}
            placeholder="Motivo de isenção"
            value={form.motivo_isencao}
            onChange={(e) =>
              setForm({ ...form, motivo_isencao: e.target.value })
            }
            required
          />
        )}

        <div className="grid grid-cols-2 gap-2">
          <input
            className={inp}
            type="date"
            value={form.vigencia_inicio}
            onChange={(e) =>
              setForm({ ...form, vigencia_inicio: e.target.value })
            }
            required
          />
          <input
            className={inp}
            type="date"
            value={form.vigencia_fim}
            onChange={(e) => setForm({ ...form, vigencia_fim: e.target.value })}
          />
        </div>

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

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm'

function Tabela({
  colunas,
  linhas,
}: {
  colunas: string[]
  linhas: ReactNode[][]
}) {
  return (
    <div className="border border-slate-200 bg-white rounded overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left">
          <tr>
            {colunas.map((c, i) => (
              <th key={i} className="px-3 py-2">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.length === 0 && (
            <tr>
              <td
                colSpan={colunas.length}
                className="px-3 py-4 text-center text-slate-500"
              >
                Sem registos.
              </td>
            </tr>
          )}
          {linhas.map((linha, i) => (
            <tr key={i} className="border-t border-slate-100">
              {linha.map((cel, j) => (
                <td key={j} className="px-3 py-2">
                  {cel}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}