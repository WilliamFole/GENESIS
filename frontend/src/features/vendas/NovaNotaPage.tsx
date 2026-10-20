import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Documento, Serie } from './types'

function formatMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function NovaNotaPage({ tipo }: { tipo: 'NC' | 'ND' }) {
  const navigate = useNavigate()
  
  const [faturas, setFaturas] = useState<Documento[]>([])
  const [series, setSeries] = useState<Serie[]>([])
  const [faturaSelId, setFaturaSelId] = useState('')
  const [serieId, setSerieId] = useState('')
  const [dataDoc, setDataDoc] = useState(() => new Date().toISOString().slice(0, 10))
  const [motivo, setMotivo] = useState('')
  
  const [erro, setErro] = useState<string | null>(null)
  const [aGravar, setAGravar] = useState(false)

  const faturaSel = faturas.find((f) => f.id === Number(faturaSelId))

  useEffect(() => {
    ;(async () => {
      try {
        const [ds, ss] = await Promise.all([
          api<Documento[]>('/api/documentos'),
          api<Serie[]>('/api/series'),
        ])
        setFaturas(ds.filter(d => ['FT', 'VD', 'FS'].includes(d.tipo_documento) && d.estado === 'finalizado'))
        setSeries(ss.filter(s => s.tipo_documento === tipo && s.ativo))
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      }
    })()
  }, [tipo])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!faturaSel) return

    setErro(null)
    setAGravar(true)
    try {
      const linhas = faturaSel.linhas.map((l) => ({
        artigo_id: l.artigo_id,
        quantidade: l.quantidade,
        preco_unitario: l.preco_unitario,
        desconto_percentual: l.desconto_percentual,
        documento_origem_linha_id: l.id,
      }))

      const payload = {
        tipo_documento: tipo,
        serie_id: Number(serieId),
        data_documento: dataDoc,
        cliente_id: faturaSel.cliente_id,
        documento_origem_id: faturaSel.id,
        observacoes: motivo,
        linhas,
      }

      const res = await api<Documento>('/api/documentos', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      await api(`/api/documentos/${res.id}/finalizar`, { method: 'POST' })
      
      // Volta para a lista correta
      navigate(tipo === 'NC' ? '/vendas/notas-credito' : '/vendas/notas-debito')
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao criar nota')
    } finally {
      setAGravar(false)
    }
  }

  const listaUrl = tipo === 'NC' ? '/vendas/notas-credito' : '/vendas/notas-debito'

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(listaUrl)}
            className="text-sm text-slate-500 hover:text-slate-800"
          >
            ← Voltar
          </button>
          <h1 className="text-lg font-semibold text-slate-800">
            Nova {tipo === 'NC' ? 'Nota de Crédito' : 'Nota de Débito'}
          </h1>
        </div>
      </div>

      {erro && (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          {erro}
        </div>
      )}

      <form onSubmit={onSubmit} className="bg-white border border-slate-200 border-t-4 border-t-slate-800 p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="block">
            <span className="block text-sm font-medium mb-1">Fatura Original *</span>
            <select
              className={inp}
              value={faturaSelId}
              onChange={(e) => setFaturaSelId(e.target.value)}
              required
            >
              <option value="">— Escolher fatura finalizada —</option>
              {faturas.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.numero_formatado} — {f.cliente_nome} ({formatMoney(f.total)} MZN)
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="block text-sm font-medium mb-1">Série *</span>
            <select
              className={inp}
              value={serieId}
              onChange={(e) => setSerieId(e.target.value)}
              required
            >
              <option value="">— Escolher série —</option>
              {series.map((s) => (
                <option key={s.id} value={s.id}>{s.prefixo}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="block text-sm font-medium mb-1">Data *</span>
            <input
              type="date"
              className={inp}
              value={dataDoc}
              onChange={(e) => setDataDoc(e.target.value)}
              required
            />
          </label>
        </div>

        {faturaSel && (
          <div className="mt-6 border-t border-slate-200 pt-4">
            <h2 className="text-sm font-semibold text-slate-800 mb-2">Linhas da Fatura Original</h2>
            <table className="w-full text-sm border border-slate-200">
              <thead className="bg-slate-50 text-left">
                <tr>
                  <th className="px-3 py-2 border-b border-slate-200">Artigo</th>
                  <th className="px-3 py-2 border-b border-slate-200">Descrição</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Qtd.</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Preço Unit.</th>
                  <th className="px-3 py-2 border-b border-slate-200 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {faturaSel.linhas.map((l) => (
                  <tr key={l.id} className="border-b border-slate-100">
                    <td className="px-3 py-2">{l.codigo}</td>
                    <td className="px-3 py-2">{l.descricao}</td>
                    <td className="px-3 py-2 text-right">{l.quantidade}</td>
                    <td className="px-3 py-2 text-right">{formatMoney(l.preco_unitario)} MZN</td>
                    <td className="px-3 py-2 text-right">{formatMoney(l.total_linha)} MZN</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-slate-500 mt-2">
              * A {tipo === 'NC' ? 'Nota de Crédito' : 'Nota de Débito'} espelha a totalidade da fatura (valores originais).
            </p>
          </div>
        )}

        <label className="block pt-2">
          <span className="block text-sm font-medium mb-1">Motivo / Justificação *</span>
          <textarea
            className={inp}
            rows={3}
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            required
            placeholder="Descreva o motivo da emissão desta nota..."
          />
        </label>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={aGravar || !faturaSel}
            className="px-4 py-2 bg-slate-900 text-white rounded text-sm disabled:opacity-50"
          >
            {aGravar ? 'A emitir...' : `Emitir ${tipo}`}
          </button>
        </div>
      </form>
    </div>
  )
}

const inp = 'w-full border border-slate-300 rounded px-3 py-2 text-sm'