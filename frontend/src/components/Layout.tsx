import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/authStore'
import { findMenuGroup, findMenuItem } from '@/features/layout/menuConfig'
import { useTabs } from '@/features/layout/tabsStore'
import { T } from '@/features/layout/theme'
import { Topbar } from './Topbar'
import { TopMenu } from './TopMenu'
import { Sidebar } from './Sidebar'
import { TabStrip } from './TabStrip'
import { StatusBar } from './StatusBar'

export function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const logout = useAuth((s) => s.logout)
  const openTab = useTabs((s) => s.open)
  const closeTab = useTabs((s) => s.close)
  const tabs = useTabs((s) => s.tabs)

  const [activeGroupId, setActiveGroupId] = useState<string | null>(
    findMenuGroup(location.pathname)?.id ?? null,
  )

  useEffect(() => {
    const item = findMenuItem(location.pathname)
    if (item?.path) {
      openTab(item.path, item.label)
    }
    const g = findMenuGroup(location.pathname)
    if (g) setActiveGroupId(g.id)
  }, [location.pathname, openTab])

  function handleSelect(path: string, label: string) {
    openTab(path, label)
    navigate(path)
  }

  function handleActivate(path: string) {
    navigate(path)
  }

  function handleClose(path: string) {
    const next = closeTab(path)
    if (path === location.pathname) {
      navigate(next ?? '/')
    }
  }

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const semAbas = tabs.length === 0

  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: T.bg,
        color: T.text,
        fontFamily: "'Open Sans', 'Segoe UI', sans-serif",
        fontSize: 13,
      }}
    >
      <Topbar />
      <TopMenu activeGroupId={activeGroupId} onSelectGroup={setActiveGroupId} />

      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <Sidebar
          activeGroupId={activeGroupId}
          onSelect={handleSelect}
          onLogout={handleLogout}
        />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <TabStrip onActivate={handleActivate} onClose={handleClose} />

          {semAbas ? (
            <WelcomeScreen />
          ) : (
            <main
              style={{
                flex: 1,
                overflow: 'auto',
                padding: 16,
                boxSizing: 'border-box',
                background: T.bg,
              }}
            >
              <div
                style={{
                  background: '#fff',
                  border: `1px solid ${T.border}`,
                  borderTop: `3px solid ${T.accent}`,
                  padding: 16,
                  minHeight: '100%',
                  boxSizing: 'border-box',
                }}
              >
                <Outlet />
              </div>
            </main>
          )}
        </div>
      </div>

      <StatusBar />
    </div>
  )
}

function WelcomeScreen() {
  return (
    <main
      style={{
        flex: 1,
        background: T.accent,
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 0,
      }}
    >
      <span
        aria-hidden
        style={{
          fontSize: 'clamp(200px, 32vw, 420px)',
          fontWeight: 800,
          letterSpacing: -20,
          lineHeight: 1,
          backgroundImage:
            'linear-gradient(180deg, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.10) 45%, rgba(255,255,255,0.00) 100%)',
          WebkitBackgroundClip: 'text',
          backgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          color: 'transparent',
          userSelect: 'none',
          pointerEvents: 'none',
        }}
      >
        SGE
      </span>
    </main>
  )
}