import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '@/lib/api'
import { useAuth } from './authStore'
import { useLicenca } from '@/features/licenca/LicencaContext'
import { api } from '@/lib/api'

const ACCENT = '#1F5BA8'
const ACCENT_SOFT = '#CFE0F5'
const BG = '#EEF1F6'
const BORDER = '#9FAEC2'
const BORDER_SOFT = '#D5DDE8'
const TEXT = '#1F2933'
const TEXT_MUTED = '#44546A'
const SOFT_BG = '#F6F8FB'

export function LoginPage() {
  const navigate = useNavigate()
  const aplicarLogin = useAuth((s) => s.login)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [aEnviar, setAEnviar] = useState(false)
  
  const { licenca } = useLicenca()
  const [recuperar, setRecuperar] = useState(false)
  const [codigo, setCodigo] = useState('')
  const [novaPass, setNovaPass] = useState('')

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setErro(null)
    setAEnviar(true)
    try {
      const token = await login(username, password)
      await aplicarLogin(token)
      navigate('/', { replace: true })
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao autenticar')
    } finally {
      setAEnviar(false)
    }
  }

  function cancelar() {
    setUsername('')
    setPassword('')
    setErro(null)
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: BG,
        color: TEXT,
        fontFamily: "'Open Sans', 'Segoe UI', sans-serif",
        fontSize: 13,
        padding: 24,
        boxSizing: 'border-box',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 900,
          display: 'flex',
          flexWrap: 'wrap',
          background: '#fff',
          border: `1px solid ${BORDER}`,
          boxShadow: '0 6px 24px rgba(31,41,51,.18)',
        }}
      >
        {/* Painel esquerdo — azul com gota e watermark */}
        <div
          style={{
            flex: '1 1 320px',
            minHeight: 460,
            background: ACCENT,
            color: '#fff',
            padding: '36px 32px 28px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Watermark SGE */}
          <div
            aria-hidden
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none',
              userSelect: 'none',
            }}
          >
            <span
              style={{
                fontSize: 260,
                fontWeight: 800,
                letterSpacing: -14,
                lineHeight: 1,
                transform: 'translateY(24px)',
                backgroundImage:
                  'linear-gradient(180deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.10) 45%, rgba(255,255,255,0.00) 100%)',
                WebkitBackgroundClip: 'text',
                backgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                color: 'transparent',
              }}
            >
              SGE
            </span>
          </div>

          {/* Título */}
          <div
            style={{
              position: 'relative',
              fontSize: 22,
              fontWeight: 800,
              letterSpacing: 0.5,
              textTransform: 'uppercase',
            }}
          >
            SGE - Faturação
          </div>

          {/* Gota de água central */}
          <div
            style={{
              position: 'relative',
              alignSelf: 'center',
              width: 168,
              height: 168,
              borderRadius: '50%',
              border: '2px solid rgba(255,255,255,.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <DropIcon size={96} />
          </div>

          {/* Rodapé com Dados da Licença */}
          <div
            style={{
              position: 'relative',
              fontSize: 12,
              color: ACCENT_SOFT,
              lineHeight: 1.6,
            }}
          >
            {licenca?.status === 'ativa' ? (
              <>
                <div style={{ fontWeight: 700, color: '#fff', fontSize: 13 }}>
                  {licenca.cliente}
                </div>
                <div>NUIT {licenca.nuit}</div>
              </>
            ) : (
              <>
                <div style={{ fontWeight: 700, color: '#fff', fontSize: 13 }}>
                  Sistema de Demonstração
                </div>
                <div>Sem licença ativa</div>
              </>
            )}
          </div>
        </div>

        {/* Painel direito — formulário */}
        <div
          style={{
            flex: '1.2 1 380px',
            padding: '40px 40px 32px',
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
            boxSizing: 'border-box',
          }}
        >
          <h1
            style={{
              margin: 0,
              fontSize: 22,
              fontWeight: 800,
              color: ACCENT,
              letterSpacing: 0.5,
              textTransform: 'uppercase',
            }}
          >
            Login - SGE
          </h1>

          <form
            onSubmit={onSubmit}
            style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
          >
            <label style={labelStyle}>
              Utilizador
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="[utilizador]"
                autoFocus
                required
                style={inputStyle}
              />
            </label>

            <label style={labelStyle}>
              Palavra-passe
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={inputStyle}
              />
            </label>

            {erro && (
              <div
                style={{
                  fontSize: 13,
                  color: '#8B1F1F',
                  background: '#FBEEEE',
                  border: '1px solid #E0B3B3',
                  padding: '8px 12px',
                  borderRadius: 3,
                }}
              >
                {erro}
              </div>
            )}

            <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
              <button
                type="submit"
                disabled={aEnviar}
                style={{
                  flex: 1,
                  height: 46,
                  border: `1px solid ${ACCENT}`,
                  background: ACCENT,
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  cursor: aEnviar ? 'wait' : 'pointer',
                  opacity: aEnviar ? 0.7 : 1,
                }}
              >
                {aEnviar ? 'A entrar…' : 'Entrar'}
              </button>
              <button
                type="button"
                onClick={cancelar}
                style={{
                  flex: 1,
                  height: 46,
                  border: `1px solid ${BORDER}`,
                  background: SOFT_BG,
                  color: TEXT,
                  fontSize: 14,
                  fontFamily: 'inherit',
                  cursor: 'pointer',
                }}
              >
                Cancelar
              </button>
            </div>

            <div className="mt-4 text-center space-y-2 text-xs text-slate-500">
              {!recuperar ? (
                <button
                  type="button"
                  onClick={() => setRecuperar(true)}
                  className="hover:text-slate-800 underline"
                >
                  Esqueceu a senha? Recuperar conta
                </button>
              ) : (
                <div className="bg-slate-50 border border-slate-200 p-3 rounded text-left space-y-2">
                  <p className="font-semibold text-slate-700">Recuperar Senha do Admin</p>
                  <input
                    type="text"
                    placeholder="Código de Recuperação"
                    className="w-full border border-slate-300 rounded px-2 py-1"
                    value={codigo}
                    onChange={(e) => setCodigo(e.target.value)}
                  />
                  <input
                    type="password"
                    placeholder="Nova Senha"
                    className="w-full border border-slate-300 rounded px-2 py-1"
                    value={novaPass}
                    onChange={(e) => setNovaPass(e.target.value)}
                  />
                  <div className="flex gap-2 justify-end">
                    <button type="button" onClick={() => setRecuperar(false)} className="text-slate-500">
                      Cancelar
                    </button>
                    <button
                      type="button"
                      onClick={async () => {
                        try {
                          await api('/api/auth/recuperar-senha', {
                            method: 'POST',
                            body: JSON.stringify({ codigo, nova_password: novaPass }),
                          })
                          alert('Senha redefinida! Verifique o terminal do backend para o novo código de recuperação.')
                          setRecuperar(false)
                        } catch (e) {
                          alert(e instanceof Error ? e.message : 'Erro')
                        }
                      }}
                      className="bg-slate-800 text-white px-3 py-1 rounded"
                    >
                      Redefinir
                    </button>
                  </div>
                </div>
              )}

              <div className="pt-2">
                {licenca?.status === 'ativa' ? (
                  <span className="text-slate-400">Licenciado para: {licenca.cliente}</span>
                ) : (
                  <span className="text-red-500 font-bold">MODO DE DEMONSTRAÇÃO</span>
                )}
              </div>
            </div>
          </form>

          <div
            style={{
              marginTop: 'auto',
              borderTop: `1px solid ${BORDER_SOFT}`,
              paddingTop: 12,
              display: 'flex',
              gap: 16,
              flexWrap: 'wrap',
              fontSize: 12,
              color: TEXT_MUTED,
            }}
          >
            <span>● Sistema de gestão empresarial</span>
            <span>Servidor: local</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function DropIcon({ size = 96 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="dropFade" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
          <stop offset="55%" stopColor="#ffffff" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <path
        d="M32 6
           C32 6 14 26 14 42
           C14 52 22 60 32 60
           C42 60 50 52 50 42
           C50 26 32 6 32 6 Z"
        stroke="url(#dropFade)"
        strokeWidth={2.4}
        strokeLinejoin="round"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M22 40
           C22 34 26 28 30 24"
        stroke="url(#dropFade)"
        strokeWidth={1.6}
        strokeLinecap="round"
        fill="none"
        opacity={0.7}
      />
    </svg>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 6,
  color: TEXT_MUTED,
  fontWeight: 600,
  fontSize: 12,
}

const inputStyle: React.CSSProperties = {
  height: 42,
  padding: '0 12px',
  border: `1px solid ${BORDER}`,
  background: '#fff',
  fontSize: 14,
  fontFamily: 'inherit',
  width: '100%',
  boxSizing: 'border-box',
}