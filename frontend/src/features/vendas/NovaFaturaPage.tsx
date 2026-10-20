import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, getToken } from '@/lib/api'
import type { Artigo, Cliente, Documento, Serie, TipoDocumentoFiscal } from './types'

type LinhaForm = {
  artigo_id: string
  quantidade: string
  desconto_percentual: string
  preco_unitario: string
}

const LINHA_VAZIA: LinhaForm = {
  artigo_id: '',
  quantidade: '1',
  desconto_percentual: '0',
  preco_unitario: '',
}

function formatMoney(v: string | number) {
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('pt-MZ', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const TIPOS_DOC = [
  { val: 'FT', label: 'FT — Fatura' },
  { val: 'VD', label: 'VD — Venda a dinheiro' },
  { val: 'FS', label: 'FS — Fatura Simplificada' },
  { val: 'COT', label: 'COT — Cotação' },
  { val: 'PRO', label: 'PRO — Proforma' },
  { val: 'GR', label: 'GR — Guia de Remessa' },
] as const

export function NovaFaturaPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const aEditar = !!id

  const [tipo, setTipo] = useState<TipoDocumentoFiscal>('FT')
  const [serieId, setSerieId] = useState('')
  const [dataDoc, setDataDoc] = useState(() => new Date().toISOString().slice(0, 10))
  const [dataVenc, setDataVenc] = useState('')
  const [condPag, setCondPag] = useState('')
  const [clienteId, setClienteId] = useState('')
  const [descGlobal, setDescGlobal] = useState('0')
  const [obs, setObs] = useState('')
  const [linhas, setLinhas] = useState<LinhaForm[]>([{ ...LINHA_VAZIA }])

  const [doc, setDoc] = useState<Documento | null>(null)
  const [series, setSeries] = useState<Serie[]>([])
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [artigos, setArtigos] = useState<Artigo[]>([])
  
  const [erro, setErro] = useState<string | null>(null)
  const [aGravar, setAGravar] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const [ss, cs, as] = await Promise.all([
          api<Serie[]>('/api/series'),
          api<Cliente[]>('/api/clientes?apenas_ativos=true'),
          api<Artigo[]>('/api/artigos?apenas_ativos=true'),
        ])
        setSeries(ss)
        setClientes(cs)
        setArtigos(as)
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro ao carregar dados')
      }
    })()
  }, [])

  useEffect(() => {
    if (id) {
      ;(async () => {
        try {
          const d = await api<Documento>(`/api/documentos/${id}`)
          setDoc(d)
          setTipo(d.tipo_documento)
          setSerieId(String(d.serie_id))
          setDataDoc(d.data_documento)
          setDataVenc(d.data_vencimento || '')
          setCondPag(d.condicao_pagamento || '')
          setClienteId(String(d.cliente_id))
          setDescGlobal(String(d.desconto_global_percentual || '0'))
          setObs(d.observacoes || '')
          setLinhas(
            d.linhas.map((l) => ({
              artigo_id: String(l.artigo_id || ''),
              quantidade: String(l.quantidade),
              desconto_percentual: String(l.desconto_percentual),
              preco_unitario: String(l.preco_unitario),
            }))
          )
        } catch (e) {
          setErro(e instanceof Error ? e.message : 'Erro ao carregar documento')
        }
      })()
    }
  }, [id])

  // Filtra as séries pelo tipo de documento escolhido
  const seriesFiltradas = useMemo(
    () => series.filter((s) => s.tipo_documento === tipo && s.ativo),
    [series, tipo]
  )

  const isNaoFiscal = ['COT', 'PRO', 'GR'].includes(tipo)

  function addLinha() {
    setLinhas((ls) => [...ls, { ...LINHA_VAZIA }])
  }
  function removeLinha(idx: number) {
    setLinhas((ls) => ls.filter((_, i) => i !== idx))
  }
  function updateLinha(idx: number, campo: keyof LinhaForm, valor: string) {
    setLinhas((ls) => {
      const copia = [...ls]
      copia[idx] = { ...copia[idx], [campo]: valor }
      if (campo === 'artigo_id' && valor) {
        const art = artigos.find((a) => a.id === Number(valor))
        if (art) copia[idx].preco_unitario = String(art.preco_unitario)
      }
      return copia
    })
  }

  const readOnly = doc?.estado === 'finalizado' || doc?.estado === 'anulado'

  async function guardar(e: FormEvent) {
    e.preventDefault()
    if (readOnly) return
    setErro(null)
    setAGravar(true)

    try {
      const payload = {
        tipo_documento: tipo,
        serie_id: Number(serieId),
        data_documento: dataDoc,
        data_vencimento: dataVenc || null,
        condicao_pagamento: condPag || null,
        cliente_id: Number(clienteId),
        desconto_global_percentual: descGlobal,
        observacoes: obs || null,
        linhas: linhas.map((l) => ({
          artigo_id: Number(l.artigo_id),
          quantidade: l.quantidade,
          desconto_percentual: l.desconto_percentual,
          preco_unitario: l.preco_unitario,
        })),
      }

      if (id) {
        await api(`/api/documentos/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
        navigate(`/vendas/faturas/${id}`)
      } else {
        const novo = await api<Documento>('/api/documentos', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        navigate(`/vendas/faturas/${novo.id}`)
      }
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao guardar')
    } finally {
      setAGravar(false)
    }
  }

  async function finalizar() {
    if (!doc) return
    setErro(null)
    setAGravar(true)
    try {
      const d = await api<Documento>(`/api/documentos/${doc.id}/finalizar`, { method: 'POST' })
      setDoc(d)
      navigate(`/vendas/faturas`)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao finalizar')
    } finally {
      setAGravar(false)
    }
  }

  async function anular() {
    if (!doc) return
    const motivo = prompt('Motivo da anulação (obrigatório, mín. 3 caracteres):')
    if (!motivo || motivo.trim().length < 3) return
    setErro(null)
    try {
      const d = await api<Documento>(`/api/documentos/${doc.id}/anular`, {
        method: 'POST',
        body: JSON.stringify({ motivo_anulacao: motivo.trim() }),
      })
      setDoc(d)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao anular')
    }
  }

  async function gerarPDF() {
    if (!doc) return
    try {
      setErro(null)
      const token = getToken()
      const res = await fetch(`/api/documentos/${doc.id}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error(await res.text())
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao gerar PDF')
    }
  }

  const total = useMemo(() => {
    let sub = 0
    for (const l of linhas) {
      const p = Number(l.preco_unitario) || 0
      const q = Number(l.quantidade) || 0
      const d = Number(l.desconto_percentual) || 0
      sub += p * q * (1 - d / 100)
    }
    const desc = sub * (Number(descGlobal) / 100)
    return sub - desc
  }, [linhas, descGlobal])

  return (
    <form onSubmit={guardar} className="space-y-4 max-w-5xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} type="button" className="text-sm text-slate-500 hover:text-slate-800">
            ← Voltar
          </button>
          <h1 className="text-lg font-semibold text-slate-800">
            {doc
              ? doc.estado === 'rascunho'
                ? 'Editar rascunho'
                : doc.estado === 'finalizado'
                ? `${tipo} ${doc.numero_formatado}`
                : `${tipo} ${doc.numero_formatado} (anulada)`
              : 'Novo documento'}
          </h1>
        </div>
      </div>

      {erro && <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">{erro}</div>}
      
      {isNaoFiscal && (
        <div className="text-sm font-bold text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2 text-center">
          ESTE DOCUMENTO NÃO SERVE DE FATURA
        </div>
      )}

      <div className="bg-white border border-slate-200 border-t-4 border-t-slate-800 p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <label className="block">
          <span className="block text-sm font-medium mb-1">Tipo</span>
          <select value={tipo} onChange={(e) => { setTipo(e.target.value as any); setSerieId('') }} disabled={readOnly} className={inp}>
            {TIPOS_DOC.map((t) => (
              <option key={t.val} value={t.val}>{t.label}</option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Série</span>
          <select value={serieId} onChange={(e) => setSerieId(e.target.value)} disabled={readOnly} required className={inp}>
            <option value="">— Escolher —</option>
            {seriesFiltradas.map((s) => (
              <option key={s.id} value={s.id}>{s.prefixo} (últ. {s.ultimo_numero})</option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Data</span>
          <input type="date" value={dataDoc} onChange={(e) => setDataDoc(e.target.value)} disabled={readOnly} required className={inp} />
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Cliente</span>
          <select value={clienteId} onChange={(e) => setClienteId(e.target.value)} disabled={readOnly} required className={inp}>
            <option value="">— Escolher —</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>{c.nome} ({c.nuit})</option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Vencimento</span>
          <input type="date" value={dataVenc} onChange={(e) => setDataVenc(e.target.value)} disabled={readOnly} className={inp} />
        </label>

        <label className="block">
          <span className="block text-sm font-medium mb-1">Cond. Pagamento</span>
          <input type="text" value={condPag} onChange={(e) => setCondPag(e.target.value)} disabled={readOnly} className={inp} />
        </label>
      </div>

      <div className="bg-white border border-slate-200 p-4">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-2 py-2">Artigo</th>
              <th className="px-2 py-2">Descrição</th>
              <th className="px-2 py-2 w-20">Qtd.</th>
              <th className="px-2 py-2 w-32">Preço Unit.</th>
              <th className="px-2 py-2 w-20">Desc.%</th>
              <th className="px-2 py-2 w-28 text-right">Total</th>
              <th className="px-2 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((l, idx) => {
              const art = artigos.find((a) => a.id === Number(l.artigo_id))
              const p = Number(l.preco_unitario) || 0
              const q = Number(l.quantidade) || 0
              const d = Number(l.desconto_percentual) || 0
              const totLinha = p * q * (1 - d / 100)
              return (
                <tr key={idx} className="border-t border-slate-100">
                  <td className="px-2 py-1">
                    <select value={l.artigo_id} onChange={(e) => updateLinha(idx, 'artigo_id', e.target.value)} disabled={readOnly} required className={inp}>
                      <option value="">—</option>
                      {artigos.map((a) => (
                        <option key={a.id} value={a.id}>{a.codigo}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-2 py-1 text-slate-600">{art?.descricao || '—'}</td>
                  <td className="px-2 py-1">
                    <input type="number" step="0.01" min="0.01" value={l.quantidade} onChange={(e) => updateLinha(idx, 'quantidade', e.target.value)} disabled={readOnly} required className={inp} />
                  </td>
                  <td className="px-2 py-1">
                    <input type="number" step="0.01" value={l.preco_unitario} onChange={(e) => updateLinha(idx, 'preco_unitario', e.target.value)} disabled={readOnly} required className={inp} />
                  </td>
                  <td className="px-2 py-1">
                    <input type="number" step="0.01" value={l.desconto_percentual} onChange={(e) => updateLinha(idx, 'desconto_percentual', e.target.value)} disabled={readOnly} className={inp} />
                  </td>
                  <td className="px-2 py-1 text-right">{formatMoney(totLinha)}</td>
                  <td className="px-2 py-1 text-right">
                    {!readOnly && linhas.length > 1 && (
                      <button type="button" onClick={() => removeLinha(idx)} className="text-red-500 hover:underline">✕</button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {!readOnly && (
          <button type="button" onClick={addLinha} className="mt-2 text-xs text-blue-600 hover:underline">
            + Adicionar linha
          </button>
        )}
      </div>

      <div className="bg-white border border-slate-200 p-4 flex flex-col items-end gap-2">
        <div className="flex justify-between w-64 text-sm">
          <span>Desconto Global %</span>
          <input type="number" step="0.01" min="0" max="100" value={descGlobal} onChange={(e) => setDescGlobal(e.target.value)} disabled={readOnly} className="w-20 border rounded px-2 text-right" />
        </div>
        <div className="flex justify-between w-64 text-lg font-bold border-t border-slate-300 pt-2 mt-2">
          <span>Total (MZN)</span>
          <span>{formatMoney(total)}</span>
        </div>
      </div>

      <label className="block">
        <span className="block text-sm font-medium mb-1">Observações</span>
        <textarea value={obs} onChange={(e) => setObs(e.target.value)} disabled={readOnly} rows={3} className={inp} />
      </label>

      {!readOnly && (
        <div className="flex justify-end gap-2">
          <button type="submit" disabled={aGravar} className="px-4 py-2 bg-slate-700 text-white rounded text-sm disabled:opacity-50">
            {aGravar ? 'A guardar...' : 'Guardar Rascunho'}
          </button>
          {doc && doc.estado === 'rascunho' && (
            <button type="button" onClick={finalizar} disabled={aGravar} className="px-4 py-2 bg-green-600 text-white rounded text-sm disabled:opacity-50">
              Finalizar
            </button>
          )}
        </div>
      )}
    </form>
  )
}

const inp = 'w-full border border-slate-300 rounded px-2 py-1 text-sm'