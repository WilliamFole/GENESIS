import { FormEvent, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { MetodoPagamento } from './types'

export function MetodosPagamentoPage() {
  const [lista, setLista] = useState<MetodoPagamento[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aberto, setAberto] = useState(false)
  const [form, setForm] = useState({ codigo: '', nome: '' })

  async function carregar() {
    try {
      setLista(await api<MetodoPagamento[]>('/api/metodos-pagamento'))
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
      await api('/api/metodos-pagamento', {
        method: 'POST',
        body: JSON.stringify({
          codigo: form.codigo.toUpperCase(),
          nome: form.nome,
        }),
      })
      setForm({ codigo: '', nome: '' })
      setAberto(false)
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function remover(id: number) {
    if (!confirm('Remover este método?')) return
    try {
      await api(`/api/metodos-pagamento/${id}`, { method: 'DELETE' })
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
          Novo método
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Código</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Ativo</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((m) => (
              <tr key={m.id} className="border-t border-slate-100">
                <td className="px-3 py-2">{m.codigo}</td>
                <td className="px-3 py-2">{m.nome}</td>
                <td className="px-3 py-2">{m.ativo ? 'Sim' : 'Não'}</td>
                <td className="px-3 py-2 text-right">
                  <button
                    onClick={() => remover(m.id)}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Remover
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {aberto && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <form
            onSubmit={criar}
            className="bg-white p-6 rounded shadow w-full max-w-sm space-y-3"
          >
            <h2 className="text-lg font-semibold">Novo método de pagamento</h2>
            <input
              className={inp}
              placeholder="Código (ex.: MB)"
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