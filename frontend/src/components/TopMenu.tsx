import { MENUS } from '@/features/layout/menuConfig'
import { T } from '@/features/layout/theme'

export function TopMenu({
  activeGroupId,
  onSelectGroup,
}: {
  activeGroupId: string | null
  onSelectGroup: (groupId: string) => void
}) {
  return (
    <nav
      style={{
        background: '#fff',
        borderBottom: `1px solid ${T.border}`,
        display: 'flex',
        gap: 2,
        padding: '0 12px',
        height: 34,
        alignItems: 'flex-end',
        overflowX: 'auto',
        flexShrink: 0,
      }}
    >
      {MENUS.map((m) => {
        const active = m.id === activeGroupId
        return (
          <button
            key={m.id}
            type="button"
            onClick={() => onSelectGroup(m.id)}
            style={{
              padding: '8px 16px',
              color: active ? T.accent : T.textMuted,
              fontWeight: active ? 700 : 400,
              background: active ? T.softBg : 'transparent',
              border: active ? `1px solid ${T.border}` : '1px solid transparent',
              borderBottom: active ? `1px solid ${T.softBg}` : '1px solid transparent',
              borderRadius: '4px 4px 0 0',
              whiteSpace: 'nowrap',
              fontSize: 13,
              fontFamily: 'inherit',
              cursor: 'pointer',
              marginBottom: -1,
            }}
          >
            {m.label}
          </button>
        )
      })}
    </nav>
  )
}