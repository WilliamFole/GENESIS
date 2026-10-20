import { FormEvent, useEffect, useMemo, useState } from 'react'
import { api } from '@/lib/api'
import type { DocumentoMin, MetodoPagamento, Pagamento, Saldo } from './types'

function fmtMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const METODOS_COM_REF = ['MPESA', 'EMOLA', 'CHQ', 'TRF']

export function PagamentosPage() {
  const [pagamentos, setPagamentos] = useState<Pagamento[]>([])
  const [documentos, setDocumentos] = useState<DocumentoMin[]>([])
  const [metodos, setMetodos] = useState<MetodoPagamento[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aberto, setAberto] = useState(false)

  async function carregar() {
    try {
      const [ps, ds, ms] = await Promise.all([
        api<Pagamento[]>('/api/pagamentos'),
        api<DocumentoMin[]>('/api/documentos'),
        api<MetodoPagamento[]>('/api/metodos-pagamento'),
      ])
      setPagamentos(ps)
      setDocumentos(
        ds.filter(
          (d) =>
            ['FT', 'VD', 'FS'].includes(d.tipo_documento) &&
            d.estado === 'finalizado',
        ),
      )
      setMetodos(ms.filter((m) => m.ativo))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    carregar()
  }, [])

  const mapaDocs = useMemo(
    () => Object.fromEntries(documentos.map((d) => [d.id, d])),
    [documentos],
  )
  const mapaMetodos = useMemo(
    () => Object.fromEntries(metodos.map((m) => [m.id, m])),
    [metodos],
  )

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4">
        <h1 className="text-lg font-semibold text-slate-800">Pagamentos</h1>
        <button
          onClick={() => setAberto(true)}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Novo pagamento
        </button>
      </div>

      {erro && <div className="text-sm text-red-600 mb-2">{erro}</div>}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Data</th>
              <th className="px-3 py-2">Documento</th>
              <th className="px-3 py-2">Cliente</th>
              <th className="px-3 py-2">Método</th>
              <th className="px-3 py-2">Referência</th>
              <th className="px-3 py-2 text-right">Valor</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {pagamentos.map((p) => {
              const doc = mapaDocs[p.documento_id]
              const met = mapaMetodos[p.metodo_pagamento_id]
              const isEstorno = Number(p.valor) < 0
              return (
                <tr key={p.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{p.data_pagamento}</td>
                  <td className="px-3 py-2">
                    {doc?.numero_formatado ?? `#${p.documento_id}`}
                  </td>
                  <td className="px-3 py-2">{doc?.cliente_nome ?? '—'}</td>
                  <td className="px-3 py-2">
                    {met?.nome ?? `#${p.metodo_pagamento_id}`}
                  </td>
                  <td className="px-3 py-2">{p.referencia ?? '—'}</td>
                  <td
                    className={`px-3 py-2 text-right ${
                      isEstorno ? 'text-red-700' : ''
                    }`}
                  >
                    {fmtMoney(p.valor)} MZN
                  </td>
                  <td className="px-3 py-2 text-right text-xs text-slate-500">
                    {isEstorno ? 'Estorno' : ''}
                  </td>
                </tr>
              )
            })}
            {pagamentos.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-center text-slate-500">
                  Sem pagamentos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {aberto && (
        <NovoPagamentoModal
          documentos={documentos}
          metodos={metodos}
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

function NovoPagamentoModal({
  documentos,
  metodos,
  onClose,
  onGravado,
}: {
  documentos: DocumentoMin[]
  metodos: MetodoPagamento[]
  onClose: () => void
  onGravado: () => void
}) {
  const [docId, setDocId] = useState('')
  const [metodoId, setMetodoId] = useState('')
  const [valor, setValor] = useState('')
  const [data, setData] = useState(() => new Date().toISOString().slice(0, 10))
  const [referencia, setReferencia] = useState('')
  const [obs, setObs] = useState('')
  const [saldo, setSaldo] = useState<Saldo | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  useEffect(() => {
    if (!docId) {
      setSaldo(null)
      return
    }
    ;(async () => {
      try {
        const s = await api<Saldo>(`/api/pagamentos/saldo/${docId}`)
        setSaldo(s)
        if (Number(s.saldo) > 0 && !valor) setValor(s.saldo)
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docId])

  const metodoAtual = metodos.find((m) => String(m.id) === metodoId)
  const precisaRef = metodoAtual
    ? METODOS_COM_REF.includes(metodoAtual.codigo.toUpperCase())
    : false

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      await api('/api/pagamentos', {
        method: 'POST',
        body: JSON.stringify({
          documento_id: Number(docId),
          metodo_pagamento_id: Number(metodoId),
          data_pagamento: data,
          valor,
          referencia: referencia || null,
          observacoes: obs || null,
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
        className="bg-white p-6 rounded shadow w-full max-w-md space-y-3 max-h-[90vh] overflow-auto"
      >
        <h2 className="text-lg font-semibold">Novo pagamento</h2>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Fatura *</span>
          <select
            className={inp}
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            required
          >
            <option value="">— Escolher —</option>
            {documentos.map((d) => (
              <option key={d.id} value={d.id}>
                {d.numero_formatado} — {d.cliente_nome} ({fmtMoney(d.total)} MZN)
              </option>
            ))}
          </select>
        </label>

        {saldo && (
          <div className="text-xs bg-slate-50 border border-slate-200 rounded p-2 space-y-0.5">
            <div className="flex justify-between">
              <span>Total:</span>
              <span>{fmtMoney(saldo.total)} MZN</span>
            </div>
            <div className="flex justify-between">
              <span>Pago:</span>
              <span>{fmtMoney(saldo.valor_pago)} MZN</span>
            </div>
            <div className="flex justify-between font-medium">
              <span>Em dívida:</span>
              <span>{fmtMoney(saldo.saldo)} MZN</span>
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Estado: {saldo.estado_pagamento}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="block text-sm font-medium mb-1">Método *</span>
            <select
              className={inp}
              value={metodoId}
              onChange={(e) => setMetodoId(e.target.value)}
              required
            >
              <option value="">— Escolher —</option>
              {metodos.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.nome}
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
        </div>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Valor *</span>
          <input
            type="number"
            step="0.01"
            min="0.01"
            className={inp}
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            required
          />
        </label>

        {precisaRef && (
          <label className="block">
            <span className="block text-sm font-medium mb-1">Referência *</span>
            <input
              className={inp}
              value={referencia}
              onChange={(e) => setReferencia(e.target.value)}
              required
            />
          </label>
        )}

        <label className="block">
          <span className="block text-sm font-medium mb-1">Observações</span>
          <textarea
            className={inp}
            rows={2}
            value={obs}
            onChange={(e) => setObs(e.target.value)}
          />
        </label>

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
            {aEnviar ? 'A guardar…' : 'Registar'}
          </button>
        </div>
      </form>
    </div>
  )
}

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm'