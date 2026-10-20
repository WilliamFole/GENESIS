import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { Perfil, useAuth } from '@/features/auth/authStore'

export function ProtectedRoute({
  children,
  perfis,
}: {
  children: ReactNode
  perfis?: Perfil[]
}) {
  const { user, carregado } = useAuth()

  if (!carregado) {
    return <div className="p-8 text-slate-500">A carregar…</div>
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (perfis && !perfis.includes(user.perfil)) {
    return <div className="p-8 text-slate-600">Sem permissão para acessar esta área.</div>
  }
  return <>{children}</>
}