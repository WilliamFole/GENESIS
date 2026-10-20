import { FormEvent, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { EstadoFecho, FechoCaixa, FechoPreview } from './types'

function fmtMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function badgeEstado(e: EstadoFecho) {
  if (e === 'aberto') return <span className="text-slate-600">Aberto</span>
  if (e === 'fechado') return <span className="text-green-700">Fechado</span>
  return <span className="text-red-700">Anulado</span>
}

export function FechosCaixaPage() {
  const [lista, setLista] = useState<FechoCaixa[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [aberto, setAberto] = useState(false)
  const [anularDe, setAnularDe] = useState<FechoCaixa | null>(null)

  async function carregar() {
    setErro(null)
    try {
      setLista(await api<FechoCaixa[]>('/api/fechos-caixa'))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  useEffect(() => {
    carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function fechar(id: number) {
    if (
      !confirm(
        'Fechar definitivamente este fecho? Não pode ser editado depois.',
      )
    )
      return
    try {
      await api(`/api/fechos-caixa/${id}/fechar`, { method: 'POST' })
      await carregar()
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-4">
        <h1 className="text-lg font-semibold text-slate-800">
          Fechos de caixa
        </h1>
        <button
          onClick={() => setAberto(true)}
          className="px-3 py-1.5 bg-slate-900 text-white rounded text-sm hover:bg-slate-800"
        >
          Fechar caixa de hoje
        </button>
      </div>

      {erro && (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2 mb-2">
          {erro}
        </div>
      )}

      <div className="border border-slate-200 bg-white rounded overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Data</th>
              <th className="px-3 py-2 text-right">Numerário</th>
              <th className="px-3 py-2 text-right">Transferência</th>
              <th className="px-3 py-2 text-right">Cartão</th>
              <th className="px-3 py-2 text-right">M-Pesa</th>
              <th className="px-3 py-2 text-right">e-Mola</th>
              <th className="px-3 py-2 text-right">Cheque</th>
              <th className="px-3 py-2 text-right">Total</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {lista.map((f) => {
              const total =
                Number(f.total_numerario) +
                Number(f.total_transferencia) +
                Number(f.total_cartao) +
                Number(f.total_mpesa) +
                Number(f.total_emola) +
                Number(f.total_cheque)
              return (
                <tr key={f.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{f.data}</td>
                  <td className="px-3 py-2 text-right">
                    {fmtMoney(f.total_numerario)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {fmtMoney(f.total_transferencia)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {fmtMoney(f.total_cartao)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {fmtMoney(f.total_mpesa)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {fmtMoney(f.total_emola)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {fmtMoney(f.total_cheque)}
                  </td>
                  <td className="px-3 py-2 text-right font-medium">
                    {fmtMoney(total)}
                  </td>
                  <td className="px-3 py-2">{badgeEstado(f.estado)}</td>
                  <td className="px-3 py-2 text-right space-x-3 whitespace-nowrap">
                    {f.estado === 'aberto' && (
                      <button
                        onClick={() => fechar(f.id)}
                        className="text-xs text-green-700 hover:underline"
                      >
                        Fechar
                      </button>
                    )}
                    {f.estado !== 'anulado' && (
                      <button
                        onClick={() => setAnularDe(f)}
                        className="text-xs text-red-600 hover:underline"
                      >
                        Anular
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
            {lista.length === 0 && (
              <tr>
                <td
                  colSpan={10}
                  className="px-3 py-4 text-center text-slate-500"
                >
                  Sem fechos registados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {aberto && (
        <NovoFechoModal
          onClose={() => setAberto(false)}
          onGravado={async () => {
            setAberto(false)
            await carregar()
          }}
        />
      )}

      {anularDe && (
        <AnularFechoModal
          fecho={anularDe}
          onClose={() => setAnularDe(null)}
          onGravado={async () => {
            setAnularDe(null)
            await carregar()
          }}
        />
      )}
    </div>
  )
}

function NovoFechoModal({
  onClose,
  onGravado,
}: {
  onClose: () => void
  onGravado: () => void
}) {
  const [data, setData] = useState(() => new Date().toISOString().slice(0, 10))
  const [obs, setObs] = useState('')
  const [preview, setPreview] = useState<FechoPreview | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  useEffect(() => {
    let cancelado = false
    ;(async () => {
      try {
        const p = await api<FechoPreview>(
          `/api/fechos-caixa/preview?data=${data}`,
        )
        if (!cancelado) setPreview(p)
      } catch (e) {
        if (!cancelado) setErro(e instanceof Error ? e.message : 'Erro')
      }
    })()
    return () => {
      cancelado = true
    }
  }, [data])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      await api('/api/fechos-caixa', {
        method: 'POST',
        body: JSON.stringify({ data, observacoes: obs || null }),
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
        <h2 className="text-lg font-semibold">Fechar caixa</h2>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Data</span>
          <input
            type="date"
            className={inp}
            value={data}
            onChange={(e) => setData(e.target.value)}
            required
          />
        </label>

        {preview && (
          <div className="text-sm bg-slate-50 border border-slate-200 rounded p-3 space-y-1">
            <h3 className="text-xs font-semibold text-slate-600 uppercase mb-2">
              Pré-visualização
            </h3>
            <Linha label="Numerário" valor={preview.total_numerario} />
            <Linha label="Transferência" valor={preview.total_transferencia} />
            <Linha label="Cartão" valor={preview.total_cartao} />
            <Linha label="M-Pesa" valor={preview.total_mpesa} />
            <Linha label="e-Mola" valor={preview.total_emola} />
            <Linha label="Cheque" valor={preview.total_cheque} />
            <div className="pt-2 mt-2 border-t border-slate-200 flex justify-between font-semibold">
              <span>Total</span>
              <span>{fmtMoney(preview.total_geral)} MZN</span>
            </div>
          </div>
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
            {aEnviar ? 'A criar…' : 'Criar fecho'}
          </button>
        </div>
      </form>
    </div>
  )
}

function AnularFechoModal({
  fecho,
  onClose,
  onGravado,
}: {
  fecho: FechoCaixa
  onClose: () => void
  onGravado: () => void
}) {
  const [motivo, setMotivo] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      await api(`/api/fechos-caixa/${fecho.id}/anular`, {
        method: 'POST',
        body: JSON.stringify({ motivo_anulacao: motivo.trim() }),
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
        className="bg-white p-6 rounded shadow w-full max-w-md space-y-3"
      >
        <h2 className="text-lg font-semibold">Anular fecho</h2>
        <p className="text-sm text-slate-600">
          Fecho de {fecho.data} — motivo obrigatório (mín. 3 caracteres)
        </p>
        <textarea
          className={inp}
          rows={3}
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          required
          minLength={3}
        />
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
            disabled={aEnviar || motivo.trim().length < 3}
            className="px-3 py-1.5 bg-red-700 text-white rounded text-sm disabled:opacity-50"
          >
            {aEnviar ? 'A anular…' : 'Anular'}
          </button>
        </div>
      </form>
    </div>
  )
}

function Linha({ label, valor }: { label: string; valor: string }) {
  return (
    <div className="flex justify-between text-slate-700">
      <span>{label}</span>
      <span>{fmtMoney(valor)} MZN</span>
    </div>
  )
}

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm'