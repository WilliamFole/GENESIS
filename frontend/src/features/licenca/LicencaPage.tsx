import { ChangeEvent, useState } from 'react'
import { getToken } from '@/lib/api'
import { useLicenca } from './LicencaContext'

export function LicencaPage() {
  const { licenca, refresh } = useLicenca()
  const [erro, setErro] = useState<string | null>(null)
  const [ok, setOk] = useState<string | null>(null)

  async function upload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setErro(null)
    setOk(null)

    const form = new FormData()
    form.append('ficheiro', file)

    try {
      const token = getToken()
      const res = await fetch('/api/licenca/upload', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      })

      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || 'Erro ao carregar licença')
      }

      setOk('Licença ativada com sucesso!')
      refresh() // Atualiza o estado global da licença
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <h1 className="text-lg font-semibold text-slate-800">Gestão de Licença</h1>

      <div
        className={`p-4 border rounded shadow-sm ${
          licenca?.status === 'ativa'
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}
      >
        <h2 className="font-bold text-lg mb-2">
          {licenca?.status === 'ativa'
            ? 'Sistema Licenciado'
            : 'Sistema Não Licenciado'}
        </h2>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-slate-500">Cliente:</div>
          <div className="font-medium">{licenca?.cliente || '—'}</div>

          <div className="text-slate-500">NUIT:</div>
          <div className="font-medium">{licenca?.nuit || '—'}</div>

          <div className="text-slate-500">Validade:</div>
          <div className="font-medium">{licenca?.validade || '—'}</div>
        </div>
      </div>

      <div className="bg-white p-4 border border-slate-200 rounded shadow-sm space-y-3">
        <h3 className="font-semibold text-slate-800">Atualizar / Renovar Licença</h3>
        <p className="text-xs text-slate-500">
          Selecione o ficheiro <code>.lic</code> fornecido pelo seu vendedor para renovar a licença.
        </p>
        <input
          type="file"
          accept=".lic"
          onChange={upload}
          className="block text-sm w-full border border-slate-300 rounded px-2 py-1"
        />
        {erro && <p className="text-red-600 text-sm">{erro}</p>}
        {ok && <p className="text-green-600 text-sm">{ok}</p>}
      </div>
    </div>
  )
}