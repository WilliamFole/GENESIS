import { useAuth } from '@/features/auth/authStore'
import { MENUS } from '@/features/layout/menuConfig'
import { T } from '@/features/layout/theme'

export function Sidebar({
  activeGroupId,
  onSelect,
  onLogout,
}: {
  activeGroupId: string | null
  onSelect: (path: string, label: string) => void
  onLogout: () => void
}) {
  const user = useAuth((s) => s.user)
  const group = MENUS.find((m) => m.id === activeGroupId)

  return (
    <aside
      style={{
        width: 208,
        flexShrink: 0,
        background: '#fff',
        borderRight: `1px solid ${T.border}`,
        padding: '12px 0',
        boxSizing: 'border-box',
        overflowY: 'auto',
      }}
    >
      {!group && (
        <div style={{ padding: '8px 16px', fontSize: 12, color: T.textMuted }}>
          Selecione um menu acima.
        </div>
      )}
      {group?.sections.map((sec) => {
        const visible = sec.items.filter(
          (i) => !i.perfis || (user && i.perfis.includes(user.perfil)),
        )
        if (visible.length === 0) return null
        return (
          <div key={sec.label}>
            <div
              style={{
                padding: '8px 16px 4px',
                fontWeight: 700,
                color: T.accent,
                textTransform: 'uppercase',
                fontSize: 11,
                letterSpacing: 0.5,
              }}
            >
              {sec.label}
            </div>
            {visible.map((item) => {
              const label = item.label
              return (
                <button
                  key={label}
                  type="button"
                  onClick={() => {
                    if (item.action === 'logout') {
                      onLogout()
                      return
                    }
                    if (item.path) onSelect(item.path, label)
                  }}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: '9px 16px 9px 28px',
                    color: T.text,
                    background: 'transparent',
                    border: 'none',
                    fontSize: 13,
                    fontFamily: 'inherit',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = T.hoverBg
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  }}
                >
                  {label}
                </button>
              )
            })}
          </div>
        )
      })}
    </aside>
  )
}