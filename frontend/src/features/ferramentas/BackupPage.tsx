import { ChangeEvent, useRef, useState } from 'react'
import { api, getToken } from '@/lib/api'

export function BackupPage() {
  const [erro, setErro] = useState<string | null>(null)
  const [ok, setOk] = useState<string | null>(null)
  const [aExportar, setAExportar] = useState(false)
  const [aImportar, setAImportar] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function exportar() {
    setErro(null)
    setOk(null)
    setAExportar(true)
    try {
      const token = getToken()
      const res = await fetch('/api/backup/exportar', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || `HTTP ${res.status}`)
      }
      const blob = await res.blob()
      const cd = res.headers.get('Content-Disposition') || ''
      const m = /filename="?([^"]+)"?/.exec(cd)
      const nome = m ? m[1] : 'genesis-backup.zip'

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = nome
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 30000)
      setOk(`Backup descarregado: ${nome}`)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setAExportar(false)
    }
  }

  async function importar(e: ChangeEvent<HTMLInputElement>) {
    const ficheiro = e.target.files?.[0]
    if (!ficheiro) return
    if (!confirm(
      'Restaurar este backup? A base de dados atual será substituída.\n\nRecomenda-se que reinicie o backend após a restauração.',
    )) return

    setErro(null)
    setOk(null)
    setAImportar(true)
    try {
      const form = new FormData()
      form.append('ficheiro', ficheiro)

      const token = getToken()
      const res = await fetch('/api/backup/importar', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      })
      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || `HTTP ${res.status}`)
      }
      const d = await res.json()
      setOk(d.mensagem || 'Backup restaurado.')
      if (fileRef.current) fileRef.current.value = ''
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setAImportar(false)
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-lg font-semibold text-slate-800">
          Backup e Restauro
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Exporta uma cópia completa da base de dados, logotipos e ficheiros
          exportados. Guarda o .zip num local seguro (pen, nuvem, segundo disco).
        </p>
      </div>

      {erro && (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          {erro}
        </div>
      )}
      {ok && (
        <div className="text-sm text-green-800 bg-green-50 border border-green-200 rounded px-3 py-2">
          {ok}
        </div>
      )}

      {/* Cartão: Exportar */}
      <div className="bg-white border border-slate-200 p-4 rounded shadow-sm space-y-3">
        <h2 className="text-sm font-semibold text-slate-800">
          1. Exportar backup
        </h2>
        <p className="text-xs text-slate-500">
          Gera um ficheiro <code>.zip</code> com a BD, uploads e um manifesto.
        </p>
        <button
          onClick={exportar}
          disabled={aExportar}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
        >
          {aExportar ? 'A gerar…' : 'Descarregar backup (.zip)'}
        </button>
      </div>

      {/* Cartão: Restaurar */}
      <div className="bg-white border border-slate-200 p-4 rounded shadow-sm space-y-3">
        <h2 className="text-sm font-semibold text-slate-800">
          2. Restaurar backup
        </h2>
        <p className="text-xs text-slate-500">
          Substitui a base de dados atual pelo conteúdo do <code>.zip</code>.
          <br />
          <strong>Recomendação:</strong> reiniciar o backend após restaurar.
        </p>

        <input
          ref={fileRef}
          type="file"
          accept=".zip"
          onChange={importar}
          disabled={aImportar}
          className="block text-sm"
        />
        {aImportar && (
          <p className="text-sm text-slate-500">A restaurar…</p>
        )}
      </div>
    </div>
  )
}