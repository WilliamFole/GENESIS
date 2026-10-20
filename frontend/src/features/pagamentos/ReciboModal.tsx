import { FormEvent, useEffect, useState } from 'react'
import { api } from '@/lib/api'

type Pagamento = {
  id: number
  valor: string
  data_pagamento: string
  recibo_id: number | null
}

type Serie = {
  id: number
  tipo_documento: string
  prefixo: string
  ativo: boolean
}

export function ReciboModal({
  documentoId,
  clienteId,
  onClose,
  onGravado,
}: {
  documentoId: number
  clienteId: number
  onClose: () => void
  onGravado: () => void
}) {
  const [pagamentos, setPagamentos] = useState<Pagamento[]>([])
  const [series, setSeries] = useState<Serie[]>([])
  const [serieId, setSerieId] = useState('')
  const [data, setData] = useState(() => new Date().toISOString().slice(0, 10))
  const [obs, setObs] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const [ps, ss] = await Promise.all([
          api<Pagamento[]>(`/api/pagamentos?documento_id=${documentoId}`),
          api<Serie[]>('/api/series'),
        ])
        setPagamentos(ps.filter((p) => !p.recibo_id && Number(p.valor) > 0))
        setSeries(ss.filter((s) => s.tipo_documento === 'RC' && s.ativo))
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    })()
  }, [documentoId])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      const rc = await api<{ id: number }>('/api/recibos', {
        method: 'POST',
        body: JSON.stringify({
          serie_id: Number(serieId),
          data_documento: data,
          cliente_id: clienteId,
          pagamentos_ids: pagamentos.map((p) => p.id),
          observacoes: obs || null,
        }),
      })
      await api(`/api/documentos/${rc.id}/finalizar`, { method: 'POST' })
      onGravado()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    } finally {
      setAEnviar(false)
    }
  }

  const total = pagamentos.reduce((s, p) => s + Number(p.valor), 0)

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <form
        onSubmit={onSubmit}
        className="bg-white p-6 rounded shadow w-full max-w-md space-y-3"
      >
        <h2 className="text-lg font-semibold">Emitir recibo</h2>

        {pagamentos.length === 0 && (
          <p className="text-sm text-slate-600">
            Não há pagamentos pendentes de recibo nesta fatura.
          </p>
        )}

        {pagamentos.length > 0 && (
          <>
            <div className="text-sm bg-slate-50 border border-slate-200 rounded p-2 space-y-1 max-h-32 overflow-auto">
              {pagamentos.map((p) => (
                <div key={p.id} className="flex justify-between">
                  <span>{p.data_pagamento}</span>
                  <span>{Number(p.valor).toFixed(2)} MZN</span>
                </div>
              ))}
              <div className="pt-1 mt-1 border-t border-slate-200 flex justify-between font-semibold">
                <span>Total</span>
                <span>{total.toFixed(2)} MZN</span>
              </div>
            </div>

            <label className="block">
              <span className="block text-sm font-medium mb-1">Série RC *</span>
              <select
                className={inp}
                value={serieId}
                onChange={(e) => setSerieId(e.target.value)}
                required
              >
                <option value="">— Escolher —</option>
                {series.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.prefixo}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="block text-sm font-medium mb-1">Data *</span>
              <input
                type="date"
                className={inp}
                value={data}
                onChange={(e) => setData(e.target.value)}
                required
              />
            </label>

            <label className="block">
              <span className="block text-sm font-medium mb-1">Observações</span>
              <textarea
                className={inp}
                rows={2}
                value={obs}
                onChange={(e) => setObs(e.target.value)}
              />
            </label>
          </>
        )}

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
            disabled={aEnviar || pagamentos.length === 0 || !serieId}
            className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
          >
            {aEnviar ? 'A emitir…' : 'Emitir recibo'}
          </button>
        </div>
      </form>
    </div>
  )
}

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm'