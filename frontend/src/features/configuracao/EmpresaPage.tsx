import { FormEvent, ReactNode, useEffect, useRef, useState } from 'react'
import { api, getToken } from '@/lib/api'
import { Empresa, RegimeIVA } from './types'

const REGIMES: { valor: RegimeIVA; label: string }[] = [
  { valor: 'geral', label: 'Geral' },
  { valor: 'simplificado', label: 'Simplificado' },
  { valor: 'isento', label: 'Isento' },
]

type FormState = {
  nuit: string
  designacao: string
  morada: string
  telefone: string
  email: string
  atividade: string
  regime_iva: RegimeIVA
  banco: string
  nib: string
  conta: string
}

const VAZIO: FormState = {
  nuit: '',
  designacao: '',
  morada: '',
  telefone: '',
  email: '',
  atividade: '',
  regime_iva: 'geral',
  banco: '',
  nib: '',
  conta: '',
}

export function EmpresaPage() {
  const [form, setForm] = useState<FormState>(VAZIO)
  const [carregado, setCarregado] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [ok, setOk] = useState<string | null>(null)
  const [aGuardar, setAGuardar] = useState(false)
  const [temLogotipo, setTemLogotipo] = useState(false)
  const [logoErro, setLogoErro] = useState<string | null>(null)
  const [logoOk, setLogoOk] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const data = await api<Empresa | null>('/api/empresa')
        if (data) {
          setForm({
            nuit: data.nuit,
            designacao: data.designacao,
            morada: data.morada,
            telefone: data.telefone ?? '',
            email: data.email ?? '',
            atividade: data.atividade ?? '',
            regime_iva: data.regime_iva,
            banco: (data as any).banco ?? '',
            nib: (data as any).nib ?? '',
            conta: (data as any).conta ?? '',
          })
          setTemLogotipo(!!data.logotipo_path)
        }
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      } finally {
        setCarregado(true)
      }
    })()
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setOk(null)
    setAGuardar(true)
    try {
      await api('/api/empresa', {
        method: 'PUT',
        body: JSON.stringify({
          ...form,
          telefone: form.telefone || null,
          email: form.email || null,
          atividade: form.atividade || null,
        }),
      })
      setOk('Dados do emitente guardados.')
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setAGuardar(false)
    }
  }

  async function enviarLogotipo(e: FormEvent) {
    e.preventDefault()
    setLogoErro(null)
    setLogoOk(null)
    const f = fileRef.current?.files?.[0]
    if (!f) {
      setLogoErro('Escolha um ficheiro.')
      return
    }
    const fd = new FormData()
    fd.append('file', f)
    try {
      const token = getToken()
      const res = await fetch('/api/empresa/logotipo', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d?.detail ?? 'Falha no upload')
      }
      setLogoOk('Logotipo atualizado.')
      setTemLogotipo(true)
      if (fileRef.current) fileRef.current.value = ''
    } catch (err) {
      setLogoErro(err instanceof Error ? err.message : 'Erro')
    }
  }

  if (!carregado) return <div className="text-sm text-slate-500">A carregar…</div>

  return (
    <div className="max-w-3xl space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Campo label="NUIT" obrigatorio>
            <input
              className={inp}
              value={form.nuit}
              onChange={(e) => setForm({ ...form, nuit: e.target.value })}
              required
            />
          </Campo>
          <Campo label="Regime de IVA" obrigatorio>
            <select
              className={inp}
              value={form.regime_iva}
              onChange={(e) =>
                setForm({ ...form, regime_iva: e.target.value as RegimeIVA })
              }
            >
              {REGIMES.map((r) => (
                <option key={r.valor} value={r.valor}>
                  {r.label}
                </option>
              ))}
            </select>
          </Campo>
        </div>

        <Campo label="Designação" obrigatorio>
          <input
            className={inp}
            value={form.designacao}
            onChange={(e) => setForm({ ...form, designacao: e.target.value })}
            required
          />
        </Campo>

        <Campo label="Morada" obrigatorio>
          <input
            className={inp}
            value={form.morada}
            onChange={(e) => setForm({ ...form, morada: e.target.value })}
            required
          />
        </Campo>

        <div className="grid grid-cols-2 gap-4">
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

        <Campo label="Atividade">
          <input
            className={inp}
            value={form.atividade}
            onChange={(e) => setForm({ ...form, atividade: e.target.value })}
          />
        </Campo>

        <h2 className="text-base font-semibold pt-4 border-t border-slate-200 mt-4">
          Dados bancários
        </h2>

        <div className="grid grid-cols-2 gap-4">
          <Campo label="Banco">
            <input
              className={inp}
              value={form.banco}
              onChange={(e) => setForm({ ...form, banco: e.target.value })}
            />
          </Campo>
          <Campo label="NIB">
            <input
              className={inp}
              value={form.nib}
              onChange={(e) => setForm({ ...form, nib: e.target.value })}
            />
          </Campo>
        </div>

        <Campo label="Conta">
          <input
            className={inp}
            value={form.conta}
            onChange={(e) => setForm({ ...form, conta: e.target.value })}
          />
        </Campo>

        {erro && <div className="text-sm text-red-600">{erro}</div>}
        {ok && <div className="text-sm text-green-700">{ok}</div>}

        <button
          type="submit"
          disabled={aGuardar}
          className="px-4 py-2 bg-slate-900 text-white rounded text-sm hover:bg-slate-800 disabled:opacity-50"
        >
          {aGuardar ? 'A guardar…' : 'Guardar'}
        </button>
      </form>

      <div className="border-t border-slate-200 pt-6">
        <h2 className="text-base font-semibold mb-3">Logótipo</h2>

        {temLogotipo && (
          <div className="mb-3">
            <img
              src={`/api/empresa/logotipo?ts=${Date.now()}`}
              alt="Logótipo"
              className="max-h-24 border border-slate-200 rounded bg-white p-1"
              onError={(e) => {
                ;(e.target as HTMLImageElement).style.display = 'none'
              }}
            />
          </div>
        )}

        <form onSubmit={enviarLogotipo} className="flex items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/svg+xml"
            className="text-sm"
          />
          <button
            type="submit"
            className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm hover:bg-slate-600"
          >
            Enviar
          </button>
        </form>
        <p className="text-xs text-slate-500 mt-2">
          PNG, JPEG ou SVG, até 2 MB.
        </p>

        {logoErro && <div className="text-sm text-red-600 mt-2">{logoErro}</div>}
        {logoOk && <div className="text-sm text-green-700 mt-2">{logoOk}</div>}
      </div>
    </div>
  )
}

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm'

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