import { T } from '@/features/layout/theme'

export function StatusBar() {
  return (
    <footer
      style={{
        background: T.sectionBg,
        borderTop: `1px solid ${T.border}`,
        padding: '6px 16px',
        display: 'flex',
        gap: 24,
        flexWrap: 'wrap',
        fontSize: 12,
        color: T.textMuted,
        flexShrink: 0,
      }}
    >
      <span>● Modo offline</span>
      <span>Cópia local em dia</span>
      <span>Aviso 40/AT/DGI/2025: submissão mensal pendente</span>
    </footer>
  )
}