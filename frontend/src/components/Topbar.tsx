import { useAuth } from '@/features/auth/authStore'
import { T } from '@/features/layout/theme'

export function Topbar() {
  const user = useAuth((s) => s.user)
  const logout = useAuth((s) => s.logout)

  return (
    <header
      style={{
        background: T.accent,
        color: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0 16px',
        height: 36,
        boxSizing: 'border-box',
        flexShrink: 0,
      }}
    >
      <strong style={{ fontSize: 14 }}>Genesis Faturação</strong>
      {user && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            fontSize: 12,
          }}
        >
          <span style={{ color: T.accentSoft }}>
            {user.nome_completo} · {user.perfil}
          </span>
          <button
            type="button"
            onClick={logout}
            style={{
              background: 'transparent',
              border: '1px solid rgba(255,255,255,.45)',
              color: '#fff',
              fontSize: 12,
              padding: '3px 10px',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            Sair
          </button>
        </div>
      )}
    </header>
  )
}