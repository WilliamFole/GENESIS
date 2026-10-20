import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { ReciboModal } from './ReciboModal'

type Pagamento = {
  id: number
  data_pagamento: string
  valor: string
  referencia: string | null
  metodo_pagamento_id: number
  recibo_id: number | null
}

type Metodo = {
  id: number
  nome: string
}

type Saldo = {
  documento_id: number
  total: string
  valor_pago: string
  saldo: string
  estado_pagamento: 'por_pagar' | 'parcial' | 'pago' | 'anulado'
}

function fmtMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const badge: Record<string, string> = {
  por_pagar: 'bg-slate-100 text-slate-700',
  parcial: 'bg-amber-100 text-amber-800',
  pago: 'bg-green-100 text-green-800',
  anulado: 'bg-red-100 text-red-800',
}

export function PagamentosBlock({
  documentoId,
  clienteId,
}: {
  documentoId: number
  clienteId: number
}) {
  const [saldo, setSaldo] = useState<Saldo | null>(null)
  const [pagamentos, setPagamentos] = useState<Pagamento[]>([])
  const [metodos, setMetodos] = useState<Metodo[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [reciboAberto, setReciboAberto] = useState(false)

  async function carregar() {
    try {
      const [s, ps, ms] = await Promise.all([
        api<Saldo>(`/api/pagamentos/saldo/${documentoId}`),
        api<Pagamento[]>(`/api/pagamentos?documento_id=${documentoId}`),
        api<Metodo[]>('/api/metodos-pagamento'),
      ])
      setSaldo(s)
      setPagamentos(ps)
      setMetodos(ms)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentoId])

  if (!saldo) return null

  const pendentesRecibo = pagamentos.filter(
    (p) => !p.recibo_id && Number(p.valor) > 0,
  )
  const podeRecibo = pendentesRecibo.length > 0

  function getMetodoNome(id: number) {
    return metodos.find((m) => m.id === id)?.nome ?? '—'
  }

  return (
    <div className="bg-white border border-slate-200 p-4 mt-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-800">Pagamentos</h2>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            badge[saldo.estado_pagamento] ?? ''
          }`}
        >
          {saldo.estado_pagamento.replace('_', ' ')}
        </span>
      </div>

      <div className="text-sm grid grid-cols-3 gap-3 mb-3">
        <div>
          <div className="text-xs text-slate-500">Total</div>
          <div className="font-medium">{fmtMoney(saldo.total)} MZN</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Pago</div>
          <div className="font-medium">{fmtMoney(saldo.valor_pago)} MZN</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Em dívida</div>
          <div className="font-medium">{fmtMoney(saldo.saldo)} MZN</div>
        </div>
      </div>

      {pagamentos.length > 0 && (
        <table className="w-full text-sm border border-slate-200 mb-3">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-2 py-1.5 border-b border-slate-200">Data</th>
              <th className="px-2 py-1.5 border-b border-slate-200">Método / Ref.</th>
              <th className="px-2 py-1.5 border-b border-slate-200">Recibo</th>
              <th className="px-2 py-1.5 border-b border-slate-200 text-right">
                Valor
              </th>
            </tr>
          </thead>
          <tbody>
            {pagamentos.map((p) => (
              <tr key={p.id} className="border-b border-slate-100">
                <td className="px-2 py-1.5">{p.data_pagamento}</td>
                <td className="px-2 py-1.5">
                  {getMetodoNome(p.metodo_pagamento_id)}
                  {p.referencia ? ` — ${p.referencia}` : ''}
                </td>
                <td className="px-2 py-1.5">
                  {p.recibo_id ? `RC #${p.recibo_id}` : '—'}
                </td>
                <td
                  className={`px-2 py-1.5 text-right ${
                    Number(p.valor) < 0 ? 'text-red-700' : ''
                  }`}
                >
                  {fmtMoney(p.valor)} MZN
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="flex gap-2">
        {Number(saldo.saldo) > 0 && saldo.estado_pagamento !== 'anulado' && (
          <button
            onClick={() => {
              window.location.href = `/tesouraria/pagamentos?doc=${documentoId}`
            }}
            className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm"
          >
            Registar pagamento
          </button>
        )}
        {podeRecibo && (
          <button
            onClick={() => setReciboAberto(true)}
            className="px-3 py-1.5 bg-slate-700 text-white rounded text-sm"
          >
            Emitir recibo
          </button>
        )}
      </div>

      {erro && <div className="text-sm text-red-600 mt-2">{erro}</div>}

      {reciboAberto && (
        <ReciboModal
          documentoId={documentoId}
          clienteId={clienteId}
          onClose={() => setReciboAberto(false)}
          onGravado={async () => {
            setReciboAberto(false)
            await carregar()
          }}
        />
      )}
    </div>
  )
}