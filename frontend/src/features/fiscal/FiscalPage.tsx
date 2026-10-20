import { useEffect, useState } from 'react'
import { api, getToken } from '@/lib/api'
import type { FicheiroExportado, GerarResponse, MapaIVA } from './types'

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]

function fmtBytes(b: number) {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / (1024 * 1024)).toFixed(2)} MB`
}

function fmtDataHora(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString('pt-MZ', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function FiscalPage() {
  const hoje = new Date()
  const [ano, setAno] = useState(hoje.getFullYear())
  const [mes, setMes] = useState(hoje.getMonth() + 1)
  const [formato, setFormato] = useState<'xml' | 'xlsx'>('xlsx')

  const [mapa, setMapa] = useState<MapaIVA | null>(null)
  const [ficheiros, setFicheiros] = useState<FicheiroExportado[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [ok, setOk] = useState<string | null>(null)
  const [aGerar, setAGerar] = useState(false)

  async function carregarMapa() {
    try {
      const dados = await api<MapaIVA>(`/api/fiscal/mapa-iva/${ano}/${mes}`)
      setMapa(dados)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  async function carregarFicheiros() {
    try {
      setFicheiros(await api<FicheiroExportado[]>('/api/fiscal/ficheiros'))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    setErro(null)
    setOk(null)
    carregarMapa()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ano, mes])

  useEffect(() => {
    carregarFicheiros()
  }, [])

  async function gerarEdeclaracao() {
    setErro(null)
    setOk(null)
    setAGerar(true)
    try {
      const r = await api<GerarResponse>(
        `/api/fiscal/edeclaracao/${ano}/${mes}?formato=${formato}`,
        { method: 'POST' },
      )
      setOk(
        `e-Declaração gerada: ${r.partes?.length ?? 1} ficheiro(s), ` +
          `${r.numero_documentos ?? 0} documento(s).`,
      )
      await carregarFicheiros()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setAGerar(false)
    }
  }

  async function gerarSaft() {
    setErro(null)
    setOk(null)
    setAGerar(true)
    try {
      const r = await api<GerarResponse>(`/api/fiscal/saft/${ano}/${mes}`, {
        method: 'POST',
      })
      setOk(
        `SAF-T gerado: ${r.nome ?? ''} (${fmtBytes(r.tamanho_bytes ?? 0)})`,
      )
      await carregarFicheiros()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setAGerar(false)
    }
  }

  async function descarregar(id: number) {
    try {
      const token = getToken()
      const r = await fetch(`/api/fiscal/ficheiros/${id}/download`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const blob = await r.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const cd = r.headers.get('content-disposition') || ''
      const m = /filename="?([^"]+)"?/.exec(cd)
      a.download = m ? m[1] : `ficheiro-${id}.bin`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(url), 30000)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao descarregar')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-800">
          Fiscal e exportação
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Gera o ficheiro mensal para submissão manual na plataforma{' '}
          <strong>e-Declaração</strong> (Aviso n.º 40/AT/DGI/2025) e o ficheiro
          SAF-T (estrutura provisória, aguarda publicação pela AT).
        </p>
      </div>

      <div className="bg-white border border-slate-200 border-t-4 border-t-slate-800 p-4 space-y-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="block">
            <span className="block text-xs font-medium text-slate-600 mb-1">Ano</span>
            <input
              type="number"
              value={ano}
              onChange={(e) => setAno(Number(e.target.value))}
              className="border border-slate-300 rounded px-3 py-1.5 text-sm w-24"
            />
          </label>
          <label className="block">
            <span className="block text-xs font-medium text-slate-600 mb-1">Mês</span>
            <select
              value={mes}
              onChange={(e) => setMes(Number(e.target.value))}
              className="border border-slate-300 rounded px-3 py-1.5 text-sm"
            >
              {MESES.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="block text-xs font-medium text-slate-600 mb-1">
              Formato e-Declaração
            </span>
            <select
              value={formato}
              onChange={(e) => setFormato(e.target.value as 'xml' | 'xlsx')}
              className="border border-slate-300 rounded px-3 py-1.5 text-sm"
            >
              <option value="xlsx">XLSX</option>
              <option value="xml">XML</option>
            </select>
          </label>
        </div>

        <div className="flex flex-wrap gap-2 pt-2">
          <button
            onClick={gerarEdeclaracao}
            disabled={aGerar}
            className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
          >
            {aGerar ? 'A gerar…' : 'Gerar e-Declaração'}
          </button>
          <button
            onClick={gerarSaft}
            disabled={aGerar}
            className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm disabled:opacity-50"
          >
            {aGerar ? 'A gerar…' : 'Gerar SAF-T'}
          </button>
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
      </div>

      <div className="bg-white border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-800 mb-3">
          Mapa de IVA — {MESES[mes - 1]} {ano}
        </h2>

        {mapa && mapa.por_taxa.length === 0 && (
          <p className="text-sm text-slate-500">
            Sem documentos fiscais finalizados neste período.
          </p>
        )}

        {mapa && mapa.por_taxa.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border border-slate-200">
              <thead className="bg-slate-100 text-left">
                <tr>
                  <th className="px-3 py-2 border-b border-slate-200">Taxa</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Liquidado base</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Liquidado IVA</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Dedutível base</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Dedutível IVA</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Saldo IVA</th>
                </tr>
              </thead>
              <tbody>
                {mapa.por_taxa.map((t) => (
                  <tr key={t.taxa} className="border-b border-slate-100">
                    <td className="px-3 py-2">{t.taxa}%</td>
                    <td className="px-3 py-2 text-right">{t.liquidado.base}</td>
                    <td className="px-3 py-2 text-right">{t.liquidado.iva}</td>
                    <td className="px-3 py-2 text-right">{t.dedutivel.base}</td>
                    <td className="px-3 py-2 text-right">{t.dedutivel.iva}</td>
                    <td className="px-3 py-2 text-right font-medium">{t.saldo.iva}</td>
                  </tr>
                ))}
                <tr className="bg-slate-50 font-semibold">
                  <td className="px-3 py-2">Total</td>
                  <td className="px-3 py-2 text-right">{mapa.totais.liquidado_base}</td>
                  <td className="px-3 py-2 text-right">{mapa.totais.liquidado_iva}</td>
                  <td className="px-3 py-2 text-right">{mapa.totais.dedutivel_base}</td>
                  <td className="px-3 py-2 text-right">{mapa.totais.dedutivel_iva}</td>
                  <td className="px-3 py-2 text-right">{mapa.totais.saldo_iva}</td>
                </tr>
              </tbody>
            </table>

            <div className="mt-3 text-xs text-slate-600 flex flex-wrap gap-4">
              <span>Documentos de liquidação: {mapa.documentos.liquidacao}</span>
              <span>Documentos de dedução (NC): {mapa.documentos.deducao}</span>
              <span>Documentos anulados: {mapa.documentos.anulados}</span>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-800">Histórico de exportações</h2>
          <button
            onClick={carregarFicheiros}
            className="text-xs text-slate-600 hover:underline"
          >
            Atualizar
          </button>
        </div>

        {ficheiros.length === 0 ? (
          <p className="text-sm text-slate-500">Sem exportações registadas.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm border border-slate-200">
              <thead className="bg-slate-100 text-left">
                <tr>
                  <th className="px-3 py-2 border-b border-slate-200">Tipo</th>
                  <th className="px-3 py-2 border-b border-slate-200">Período</th>
                  <th className="px-3 py-2 border-b border-slate-200">Formato</th>
                  <th className="px-3 py-2 border-b border-slate-200">Parte</th>
                  <th className="px-3 py-2 border-b border-slate-200">Docs</th>
                  <th className="px-3 py-2 border-b border-slate-200">Tamanho</th>
                  <th className="px-3 py-2 border-b border-slate-200">Data</th>
                  <th className="px-3 py-2 border-b border-slate-200"></th>
                </tr>
              </thead>
              <tbody>
                {ficheiros.map((f) => (
                  <tr key={f.id} className="border-b border-slate-100">
                    <td className="px-3 py-2">{f.tipo}</td>
                    <td className="px-3 py-2">
                      {String(f.periodo_ano)}-{String(f.periodo_mes).padStart(2, '0')}
                    </td>
                    <td className="px-3 py-2">{f.formato.toUpperCase()}</td>
                    <td className="px-3 py-2">{f.numero_parte}/{f.total_partes}</td>
                    <td className="px-3 py-2">{f.numero_documentos}</td>
                    <td className="px-3 py-2">{fmtBytes(f.tamanho_bytes)}</td>
                    <td className="px-3 py-2">{fmtDataHora(f.criado_em)}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => descarregar(f.id)}
                        className="text-xs text-slate-700 hover:underline"
                      >
                        Descarregar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}