import { FormEvent, ReactNode, useEffect, useState } from 'react'
import { api } from '@/lib/api'

export type Cliente = {
  id: number
  numero: number | null
  numero_formatado: string
  nuit: string
  nome: string
  morada: string
  telefone: string | null
  email: string | null
  ativo: boolean
  consumidor_final: boolean
  saldo_inicial: string
  criado_em: string
  atualizado_em: string
}

type Movimento = {
  data: string
  documento_tipo: string
  documento_numero: string
  descricao: string
  debito: string
  credito: string
  saldo: string
}

type ContaCorrente = {
  cliente_id: number
  cliente_nome: string
  saldo: string
  movimentos: Movimento[]
}

type FormState = {
  nuit: string
  nome: string
  morada: string
  telefone: string
  email: string
  saldo_inicial: string
}

const VAZIO: FormState = {
  nuit: '',
  nome: '',
  morada: '',
  telefone: '',
  email: '',
  saldo_inicial: '0',
}

export function ClientesPage() {
  const [lista, setLista] = useState<Cliente[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [busca, setBusca] = useState('')
  const [soAtivos, setSoAtivos] = useState(false)
  const [aberto, setAberto] = useState(false)
  const [editar, setEditar] = useState<Cliente | null>(null)
  const [contaDe, setContaDe] = useState<Cliente | null>(null)

  async function carregar() {
    try {
      const params = new URLSearchParams()
      if (busca.trim()) params.set('q', busca.trim())
      if (soAtivos) params.set('apenas_ativos', 'true')
      const qs = params.toString()
      const url = qs ? `/api/clientes?${qs}` : '/api/clientes'
      setLista(await api<Cliente[]>(url))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    const t = setTimeout(carregar, 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busca, soAtivos])

  async function alternarAtivo(c: Cliente) {
    if (c.consumidor_final) return
    try {
      await api(`/api/clientes/${c.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ativo: !c.ativo }),
      })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function remover(c: Cliente) {
    if (!confirm(`Apagar o cliente "${c.nome}"?`)) return
    try {
      await api(`/api/clientes/${c.id}`, { method: 'DELETE' })
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
            placeholder="Buscar por nome ou NUIT"
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
          Novo cliente
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Nº / NUIT</th>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">Telefone</th>
              <th className="px-3 py-2 text-right">Saldo Inicial</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((c) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="px-3 py-2">
                  <div className="font-medium text-slate-800">{c.numero_formatado}</div>
                  <div className="text-xs text-slate-500">{c.nuit}</div>
                </td>
                <td className="px-3 py-2">
                  {c.nome}
                  {c.consumidor_final && (
                    <span className="ml-2 text-xs text-slate-500">
                      (reservado)
                    </span>
                  )}
                </td>
                <td className="px-3 py-2">{c.telefone ?? ''}</td>
                <td className="px-3 py-2 text-right">
                  {Number(c.saldo_inicial).toLocaleString('pt-MZ', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}{' '}
                  MZN
                </td>
                <td className="px-3 py-2">
                  {c.ativo ? (
                    'Ativo'
                  ) : (
                    <span className="text-amber-700">Inativo</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right space-x-3 whitespace-nowrap">
                  <button
                    onClick={() => {
                      setEditar(c)
                      setAberto(true)
                    }}
                    className="text-xs text-slate-700 hover:underline"
                  >
                    Editar
                  </button>
                  <button
                    onClick={() => setContaDe(c)}
                    className="text-xs text-slate-700 hover:underline"
                  >
                    Conta corrente
                  </button>
                  {!c.consumidor_final && (
                    <>
                      <button
                        onClick={() => alternarAtivo(c)}
                        className="text-xs text-amber-700 hover:underline"
                      >
                        {c.ativo ? 'Inativar' : 'Reativar'}
                      </button>
                      <button
                        onClick={() => remover(c)}
                        className="text-xs text-red-600 hover:underline"
                      >
                        Apagar
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {lista.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-3 py-4 text-center text-slate-500"
                >
                  Sem clientes.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {aberto && (
        <ClienteForm
          inicial={
            editar
              ? {
                  nuit: editar.nuit,
                  nome: editar.nome,
                  morada: editar.morada,
                  telefone: editar.telefone ?? '',
                  email: editar.email ?? '',
                  saldo_inicial: editar.saldo_inicial,
                }
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

      {contaDe && (
        <ContaCorrenteModal
          cliente={contaDe}
          onClose={() => setContaDe(null)}
        />
      )}
    </div>
  )
}

function ClienteForm({
  inicial,
  edicao,
  onClose,
  onGravado,
}: {
  inicial: FormState
  edicao: Cliente | null
  onClose: () => void
  onGravado: () => void
}) {
  const consumidorFinal = edicao?.consumidor_final === true
  const [form, setForm] = useState<FormState>(inicial)
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      if (consumidorFinal) {
        await api(`/api/clientes/${edicao!.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            telefone: form.telefone || null,
            email: form.email || null,
          }),
        })
      } else if (edicao) {
        await api(`/api/clientes/${edicao.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            nuit: form.nuit,
            nome: form.nome,
            morada: form.morada,
            telefone: form.telefone || null,
            email: form.email || null,
            saldo_inicial: form.saldo_inicial,
          }),
        })
      } else {
        await api('/api/clientes', {
          method: 'POST',
          body: JSON.stringify({
            nuit: form.nuit,
            nome: form.nome,
            morada: form.morada,
            telefone: form.telefone || null,
            email: form.email || null,
            saldo_inicial: form.saldo_inicial,
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

  const disabled = consumidorFinal

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <form
        onSubmit={onSubmit}
        className="bg-white p-6 rounded shadow w-full max-w-md space-y-3"
      >
        <h2 className="text-lg font-semibold">
          {edicao ? 'Editar cliente' : 'Novo cliente'}
        </h2>

        {consumidorFinal && (
          <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
            Cliente reservado. Só é possível editar telefone e email.
          </div>
        )}

        <Campo label="NUIT" obrigatorio={!consumidorFinal}>
          <input
            className={inp}
            value={form.nuit}
            onChange={(e) =>
              setForm({ ...form, nuit: e.target.value.replace(/\D/g, '') })
            }
            maxLength={9}
            minLength={9}
            required={!consumidorFinal}
            disabled={disabled}
          />
        </Campo>

        <Campo label="Nome" obrigatorio={!consumidorFinal}>
          <input
            className={inp}
            value={form.nome}
            onChange={(e) => setForm({ ...form, nome: e.target.value })}
            required={!consumidorFinal}
            disabled={disabled}
          />
        </Campo>

        <Campo label="Morada" obrigatorio={!consumidorFinal}>
          <input
            className={inp}
            value={form.morada}
            onChange={(e) => setForm({ ...form, morada: e.target.value })}
            required={!consumidorFinal}
            disabled={disabled}
          />
        </Campo>

        <div className="grid grid-cols-2 gap-3">
          <Campo label="Telefone">
            <input
              className={inp}
              value={form.telefone}
              onChange={(e) => setForm({ ...form, telefone: e.target.value })}
            />
          </Campo>
          <Campo label="Email">
            <input
              type="email"
              className={inp}
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </Campo>
        </div>

        <Campo label="Saldo Inicial (MZN)">
          <input
            type="number"
            step="0.01"
            className={inp}
            value={form.saldo_inicial}
            onChange={(e) => setForm({ ...form, saldo_inicial: e.target.value })}
            disabled={disabled}
          />
        </Campo>

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

function ContaCorrenteModal({
  cliente,
  onClose,
}: {
  cliente: Cliente
  onClose: () => void
}) {
  const [dados, setDados] = useState<ContaCorrente | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        setDados(
          await api<ContaCorrente>(
            `/api/clientes/${cliente.id}/conta-corrente`,
          ),
        )
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    })()
  }, [cliente.id])

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white p-6 rounded shadow w-full max-w-2xl space-y-3">
        <h2 className="text-lg font-semibold">
          Conta corrente — {cliente.nome}
        </h2>
        <p className="text-xs text-slate-500">
          Saldo atual:{' '}
          <span className="font-medium text-slate-800">
            {dados ? `${dados.saldo} MZN` : '…'}
          </span>
        </p>

        {erro && <div className="text-sm text-red-600">{erro}</div>}

        <div className="border border-slate-200 rounded overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-left">
              <tr>
                <th className="px-3 py-2">Data</th>
                <th className="px-3 py-2">Documento</th>
                <th className="px-3 py-2">Descrição</th>
                <th className="px-3 py-2 text-right">Débito</th>
                <th className="px-3 py-2 text-right">Crédito</th>
                <th className="px-3 py-2 text-right">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {dados?.movimentos.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-3 py-4 text-center text-slate-500"
                  >
                    Ainda não existem movimentos.
                  </td>
                </tr>
              )}
              {dados?.movimentos.map((m, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="px-3 py-2">{m.data}</td>
                  <td className="px-3 py-2">
                    {m.documento_tipo} {m.documento_numero}
                  </td>
                  <td className="px-3 py-2">{m.descricao}</td>
                  <td className="px-3 py-2 text-right">{m.debito}</td>
                  <td className="px-3 py-2 text-right">{m.credito}</td>
                  <td className="px-3 py-2 text-right">{m.saldo}</td>
                </tr>
              ))}
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

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm disabled:bg-slate-100'

function Campo({
  label,
  children,
  obrigatorio,
}: {
  label: string
  children: ReactNode
  obrigatorio?: boolean
}) {
  return (
    <label className="block">
      <span className="block text-sm font-medium mb-1">
        {label} {obrigatorio && <span className="text-red-600">*</span>}
      </span>
      {children}
    </label>
  )
}