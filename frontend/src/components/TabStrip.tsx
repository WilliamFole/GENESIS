import { useTabs } from '@/features/layout/tabsStore'
import { T } from '@/features/layout/theme'

export function TabStrip({
  onActivate,
  onClose,
}: {
  onActivate: (path: string) => void
  onClose: (path: string) => void
}) {
  const tabs = useTabs((s) => s.tabs)
  const activePath = useTabs((s) => s.activePath)

  if (tabs.length === 0) return null

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'stretch',
        background: T.sectionBg,
        borderBottom: `1px solid ${T.border}`,
        overflowX: 'auto',
        flexShrink: 0,
        minHeight: 34,
      }}
    >
      {tabs.map((t) => {
        const active = t.path === activePath
        return (
          <div
            key={t.path}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '0 12px',
              height: 34,
              background: active ? '#fff' : 'transparent',
              borderRight: `1px solid ${T.border}`,
              borderTop: active ? `2px solid ${T.accent}` : '2px solid transparent',
              color: active ? T.accent : T.textMuted,
              fontWeight: active ? 600 : 400,
              fontSize: 12.5,
              whiteSpace: 'nowrap',
              cursor: 'pointer',
            }}
            onClick={() => onActivate(t.path)}
          >
            <span>{t.label}</span>
            <button
              type="button"
              title="Fechar"
              onClick={(e) => {
                e.stopPropagation()
                onClose(t.path)
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: active ? T.textMuted : '#9AA7B8',
                fontSize: 14,
                lineHeight: 1,
                cursor: 'pointer',
                padding: 0,
                width: 16,
                height: 16,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontFamily: 'inherit',
              }}
            >
              ×
            </button>
          </div>
        )
      })}
    </div>
  )
}