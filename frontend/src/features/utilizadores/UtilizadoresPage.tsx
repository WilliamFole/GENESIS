import { FormEvent, useEffect, useState } from 'react'
import { api } from '@/lib/api'

type Perfil = 'administrador' | 'faturacao' | 'contabilista' | 'auditor'

type Utilizador = {
  id: number
  username: string
  nome_completo: string
  perfil: Perfil
  ativo: boolean
}

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm disabled:bg-slate-100'

export function UtilizadoresPage() {
  const [lista, setLista] = useState<Utilizador[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aberto, setAberto] = useState(false)
  const [editar, setEditar] = useState<Utilizador | null>(null)

  async function carregar() {
    try {
      setLista(await api<Utilizador[]>('/api/utilizadores'))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">Utilizadores</h1>
        <button
          onClick={() => {
            setEditar(null)
            setAberto(true)
          }}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
        >
          Novo Utilizador
        </button>
      </div>

      {erro && <div className="text-sm text-red-600">{erro}</div>}

      <div className="bg-white border border-slate-200 rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Nome Completo</th>
              <th className="px-3 py-2">Username</th>
              <th className="px-3 py-2">Perfil</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="px-3 py-2 font-medium">{u.nome_completo}</td>
                <td className="px-3 py-2">{u.username}</td>
                <td className="px-3 py-2 capitalize">{u.perfil}</td>
                <td className="px-3 py-2">
                  {u.ativo ? (
                    <span className="text-green-700">Ativo</span>
                  ) : (
                    <span className="text-red-700">Inativo</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right">
                  <button
                    onClick={() => {
                      setEditar(u)
                      setAberto(true)
                    }}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {aberto && (
        <FormularioUtilizador
          inicial={editar}
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

function FormularioUtilizador({
  inicial,
  onClose,
  onGravado,
}: {
  inicial: Utilizador | null
  onClose: () => void
  onGravado: () => void
}) {
  const [username, setUsername] = useState(inicial?.username ?? '')
  const [nomeCompleto, setNomeCompleto] = useState(inicial?.nome_completo ?? '')
  const [perfil, setPerfil] = useState<Perfil>(inicial?.perfil ?? 'faturacao')
  const [ativo, setAtivo] = useState(inicial?.ativo ?? true)
  const [password, setPassword] = useState('')
  
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      if (inicial) {
        // Editar
        const payload: any = { nome_completo: nomeCompleto, perfil, ativo }
        if (password) payload.password = password
        
        await api(`/api/utilizadores/${inicial.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
      } else {
        // Criar
        await api('/api/utilizadores', {
          method: 'POST',
          body: JSON.stringify({
            username,
            nome_completo: nomeCompleto,
            perfil,
            ativo,
            password,
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
      <form onSubmit={onSubmit} className="bg-white p-6 rounded shadow w-full max-w-md space-y-3">
        <h2 className="text-lg font-semibold">
          {inicial ? 'Editar Utilizador' : 'Novo Utilizador'}
        </h2>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Username</span>
          <input
            className={inp}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={!!inicial} // Não permite alterar o username depois de criado
            required
          />
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Nome Completo</span>
          <input
            className={inp}
            value={nomeCompleto}
            onChange={(e) => setNomeCompleto(e.target.value)}
            required
          />
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">
            {inicial ? 'Nova Password (deixar em branco para manter)' : 'Password'}
          </span>
          <input
            type="password"
            className={inp}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required={!inicial}
          />
        </label>

        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="block text-sm font-medium mb-1">Perfil</span>
            <select
              className={inp}
              value={perfil}
              onChange={(e) => setPerfil(e.target.value as Perfil)}
            >
              <option value="administrador">Administrador</option>
              <option value="faturacao">Faturação</option>
              <option value="contabilista">Contabilista</option>
              <option value="auditor">Auditor</option>
            </select>
          </label>

          <label className="block">
            <span className="block text-sm font-medium mb-1">Estado</span>
            <select
              className={inp}
              value={ativo ? 'true' : 'false'}
              onChange={(e) => setAtivo(e.target.value === 'true')}
            >
              <option value="true">Ativo</option>
              <option value="false">Inativo</option>
            </select>
          </label>
        </div>

        {erro && <div className="text-sm text-red-600">{erro}</div>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-3 py-1.5 text-sm text-slate-600">
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