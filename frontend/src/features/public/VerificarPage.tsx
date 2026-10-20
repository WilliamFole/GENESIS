import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

type Resposta = {
  valido: boolean
  motivo: string | null
  codigo: string
  numero_formatado?: string
  data?: string
  total?: string
  cliente_nome?: string
  estado?: string
  emitente_nome?: string | null
  emitente_nuit?: string | null
}

function formatMoney(v: string | undefined) {
  if (!v) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return v
  return n.toLocaleString('pt-MZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function VerificarPage() {
  const { codigo } = useParams<{ codigo: string }>()
  const [res, setRes] = useState<Resposta | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregado, setCarregado] = useState(false)

  useEffect(() => {
    if (!codigo) return
    ;(async () => {
      try {
        const r = await fetch(`/api/public/verificar/${codigo}`)
        if (!r.ok) {
          const t = await r.text()
          throw new Error(t || `HTTP ${r.status}`)
        }
        setRes(await r.json())
      } catch (e) {
        setErro(e instanceof Error ? e.message : 'Erro')
      } finally {
        setCarregado(true)
      }
    })()
  }, [codigo])

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#EEF1F6',
        fontFamily: "'Open Sans','Segoe UI',sans-serif",
        padding: 24,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 640,
          background: '#fff',
          border: '1px solid #9FAEC2',
          boxShadow: '0 6px 24px rgba(31,41,51,.18)',
        }}
      >
        <div style={{ background: '#1F5BA8', color: '#fff', padding: '12px 20px' }}>
          <strong>Verificação de autenticidade · Genesis</strong>
        </div>

        <div style={{ padding: 24 }}>
          {!carregado && <p>A verificar…</p>}
          {erro && (
            <div className="text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2 text-sm">
              {erro}
            </div>
          )}

          {res && !erro && (
            <>
              {res.valido ? (
                <div
                  style={{
                    background: '#E6F5E6',
                    border: '1px solid #79B779',
                    color: '#1E5C1E',
                    padding: 14,
                    borderRadius: 4,
                    marginBottom: 16,
                    fontSize: 15,
                    fontWeight: 600,
                  }}
                >
                  ✓ Documento autêntico
                </div>
              ) : (
                <div
                  style={{
                    background: '#FBEEEE',
                    border: '1px solid #E0B3B3',
                    color: '#8B1F1F',
                    padding: 14,
                    borderRadius: 4,
                    marginBottom: 16,
                    fontSize: 15,
                    fontWeight: 600,
                  }}
                >
                  ✗ {res.motivo ?? 'Documento inválido'}
                </div>
              )}

              {res.numero_formatado && (
                <table style={{ width: '100%', fontSize: 14, borderCollapse: 'collapse' }}>
                  <tbody>
                    <Linha k="Documento" v={res.numero_formatado} />
                    <Linha k="Data" v={res.data ?? '—'} />
                    <Linha k="Cliente" v={res.cliente_nome ?? '—'} />
                    <Linha k="Total" v={`${formatMoney(res.total)} MZN`} />
                    {res.estado && (
                      <Linha k="Estado" v={res.estado === 'anulado' ? 'Anulado' : 'Finalizado'} />
                    )}
                    {res.emitente_nome && <Linha k="Emitente" v={res.emitente_nome} />}
                    {res.emitente_nuit && <Linha k="NUIT" v={res.emitente_nuit} />}
                  </tbody>
                </table>
              )}

              <p style={{ fontSize: 11, color: '#888', marginTop: 24 }}>
                Código de verificação: <code>{res.codigo}</code>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function Linha({ k, v }: { k: string; v: string }) {
  return (
    <tr>
      <td style={{ padding: '6px 0', color: '#44546A', width: 140 }}>{k}</td>
      <td style={{ padding: '6px 0', color: '#1F2933', fontWeight: 500 }}>{v}</td>
    </tr>
  )
}