import { FormEvent, ReactNode, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Moeda, TaxaCambio } from './types'

type MoedaForm = { codigo: string; nome: string; simbolo: string }
type TaxaForm = { taxa: string; vigencia_inicio: string; vigencia_fim: string }

const hoje = () => new Date().toISOString().slice(0, 10)

export function MoedasPage() {
  const [lista, setLista] = useState<Moeda[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [formAberto, setFormAberto] = useState(false)
  const [taxasDe, setTaxasDe] = useState<Moeda | null>(null)

  async function carregar() {
    try {
      setLista(await api<Moeda[]>('/api/moedas'))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }
  useEffect(() => {
    carregar()
  }, [])

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setFormAberto(true)}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Nova moeda
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <Tabela
        colunas={['Código', 'Nome', 'Símbolo', 'Base', 'Ativo', '']}
        linhas={lista.map((m) => [
          m.codigo,
          m.nome,
          m.simbolo ?? '',
          m.base ? 'Sim' : '',
          m.ativo ? 'Sim' : 'Não',
          <div key={m.id} className="text-right">
            {!m.base && (
              <button
                onClick={() => setTaxasDe(m)}
                className="text-xs text-slate-700 hover:underline"
              >
                Taxas de câmbio
              </button>
            )}
          </div>,
        ])}
      />

      {formAberto && (
        <MoedaForm
          onClose={() => setFormAberto(false)}
          onGravado={async () => {
            setFormAberto(false)
            await carregar()
          }}
        />
      )}

      {taxasDe && (
        <TaxasModal moeda={taxasDe} onClose={() => setTaxasDe(null)} />
      )}
    </div>
  )
}

function MoedaForm({
  onClose,
  onGravado,
}: {
  onClose: () => void
  onGravado: () => void
}) {
  const [form, setForm] = useState<MoedaForm>({ codigo: '', nome: '', simbolo: '' })
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      await api('/api/moedas', {
        method: 'POST',
        body: JSON.stringify({
          codigo: form.codigo.toUpperCase(),
          nome: form.nome,
          simbolo: form.simbolo || null,
        }),
      })
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
        className="bg-white p-6 rounded shadow w-full max-w-sm space-y-3"
      >
        <h2 className="text-lg font-semibold">Nova moeda</h2>
        <input
          className={inp}
          placeholder="Código ISO (3 letras)"
          maxLength={3}
          value={form.codigo}
          onChange={(e) =>
            setForm({ ...form, codigo: e.target.value.toUpperCase() })
          }
          required
        />
        <input
          className={inp}
          placeholder="Nome"
          value={form.nome}
          onChange={(e) => setForm({ ...form, nome: e.target.value })}
          required
        />
        <input
          className={inp}
          placeholder="Símbolo"
          value={form.simbolo}
          onChange={(e) => setForm({ ...form, simbolo: e.target.value })}
        />
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

function TaxasModal({ moeda, onClose }: { moeda: Moeda; onClose: () => void }) {
  const [lista, setLista] = useState<TaxaCambio[]>([])
  const [form, setForm] = useState<TaxaForm>({
    taxa: '',
    vigencia_inicio: hoje(),
    vigencia_fim: '',
  })
  const [erro, setErro] = useState<string | null>(null)

  async function carregar() {
    try {
      setLista(await api<TaxaCambio[]>(`/api/moedas/${moeda.id}/taxas`))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }
  useEffect(() => {
    carregar()
  }, [moeda.id])

  async function adicionar(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    try {
      await api(`/api/moedas/${moeda.id}/taxas`, {
        method: 'POST',
        body: JSON.stringify({
          moeda_id: moeda.id,
          taxa: form.taxa,
          vigencia_inicio: form.vigencia_inicio,
          vigencia_fim: form.vigencia_fim || null,
        }),
      })
      setForm({ taxa: '', vigencia_inicio: hoje(), vigencia_fim: '' })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function remover(id: number) {
    if (!confirm('Remover esta taxa?')) return
    try {
      await api(`/api/moedas/taxas/${id}`, { method: 'DELETE' })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white p-6 rounded shadow w-full max-w-lg space-y-3">
        <h2 className="text-lg font-semibold">
          Taxas de câmbio — {moeda.codigo}
        </h2>
        <p className="text-xs text-slate-500">
          1 {moeda.codigo} = N MZN (vigência por data)
        </p>

        <form onSubmit={adicionar} className="grid grid-cols-3 gap-2 items-end">
          <input
            className={inp}
            placeholder="Taxa (MZN)"
            type="number"
            step="0.000001"
            value={form.taxa}
            onChange={(e) => setForm({ ...form, taxa: e.target.value })}
            required
          />
          <input
            className={inp}
            type="date"
            value={form.vigencia_inicio}
            onChange={(e) =>
              setForm({ ...form, vigencia_inicio: e.target.value })
            }
            required
          />
          <button
            type="submit"
            className="px-3 py-2 bg-slate-900 text-white rounded text-sm"
          >
            Adicionar
          </button>
        </form>

        {erro && <div className="text-sm text-red-600">{erro}</div>}

        <div className="border border-slate-200 rounded overflow-hidden max-h-72 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Taxa</th>
                <th className="px-3 py-2">Vigência</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {lista.map((t) => (
                <tr key={t.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{t.taxa}</td>
                  <td className="px-3 py-2">
                    {t.vigencia_inicio}
                    {t.vigencia_fim ? ` → ${t.vigencia_fim}` : ''}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => remover(t.id)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
              {lista.length === 0 && (
                <tr>
                  <td
                    colSpan={3}
                    className="px-3 py-3 text-center text-slate-500"
                  >
                    Sem taxas registadas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-slate-600"
          >
            Fechar
          </button>
        </div>
      </div>
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