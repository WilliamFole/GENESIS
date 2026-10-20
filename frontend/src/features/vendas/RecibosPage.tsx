import { useEffect, useState } from 'react'
import { api, getToken } from '@/lib/api'

type LinhaRecibo = {
  id: number
  codigo: string
  descricao: string
  total_linha: string
}

type Recibo = {
  id: number
  numero_formatado: string
  data_documento: string
  cliente_nome: string
  cliente_nuit: string
  total: string
  estado: string
  linhas: LinhaRecibo[]
}

function fmtMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function RecibosPage() {
  const [recibos, setRecibos] = useState<Recibo[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [selecionado, setSelecionado] = useState<Recibo | null>(null)

  useEffect(() => {
    ;(async () => {
      try {
        const dados = await api<Recibo[]>('/api/recibos')
        setRecibos(Array.isArray(dados) ? dados : [])
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro ao carregar recibos')
      }
    })()
  }, [])

  async function imprimirPDF(id: number) {
    try {
      const token = getToken()
      const res = await fetch(`/api/documentos/${id}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Erro ao gerar PDF')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-800">Recibos (RC)</h1>
      </div>

      {erro && (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          {erro}
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Data</th>
              <th className="px-3 py-2">Nº Recibo</th>
              <th className="px-3 py-2">Cliente</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2 text-right">Total</th>
              <th className="px-3 py-2 text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            {recibos.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                <td className="px-3 py-2">{r.data_documento}</td>
                <td className="px-3 py-2 font-medium">{r.numero_formatado}</td>
                <td className="px-3 py-2">{r.cliente_nome}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${r.estado === 'finalizado' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-700'}`}>
                    {r.estado}
                  </span>
                </td>
                <td className="px-3 py-2 text-right">{fmtMoney(r.total)} MZN</td>
                <td className="px-3 py-2 text-right space-x-3 whitespace-nowrap">
                  <button
                    onClick={() => setSelecionado(r)}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Ver detalhe
                  </button>
                  <button
                    onClick={() => imprimirPDF(r.id)}
                    className="text-xs text-slate-700 hover:underline"
                  >
                    PDF
                  </button>
                </td>
              </tr>
            ))}
            {recibos.length === 0 && (
              <tr>
                <td colSpan={6} className="px-3 py-4 text-center text-slate-500">
                  Sem recibos emitidos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selecionado && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white p-6 rounded shadow w-full max-w-lg space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-lg font-semibold">
                  Recibo {selecionado.numero_formatado}
                </h2>
                <p className="text-sm text-slate-500">
                  {selecionado.data_documento} — {selecionado.cliente_nome} (NUIT: {selecionado.cliente_nuit})
                </p>
              </div>
              <button
                onClick={() => setSelecionado(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <table className="w-full text-sm border border-slate-200">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-2 py-1.5 border-b border-slate-200">Fatura Liquidada</th>
                  <th className="px-2 py-1.5 border-b border-slate-200 text-right">Valor</th>
                </tr>
              </thead>
              <tbody>
                {selecionado.linhas.map((l) => (
                  <tr key={l.id} className="border-b border-slate-100">
                    <td className="px-2 py-1.5">
                      <div className="font-medium">{l.codigo}</div>
                      <div className="text-xs text-slate-500">{l.descricao}</div>
                    </td>
                    <td className="px-2 py-1.5 text-right font-medium">
                      {fmtMoney(l.total_linha)} MZN
                    </td>
                  </tr>
                ))}
                <tr className="bg-slate-50 font-semibold">
                  <td className="px-2 py-2">Total</td>
                  <td className="px-2 py-2 text-right">
                    {fmtMoney(selecionado.total)} MZN
                  </td>
                </tr>
              </tbody>
            </table>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => imprimirPDF(selecionado.id)}
                className="px-4 py-2 bg-slate-900 text-white rounded text-sm"
              >
                Imprimir PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}