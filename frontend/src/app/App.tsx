import { useEffect } from 'react'
import { RouterProvider } from 'react-router-dom'
import { router } from './router'
import { LicencaProvider } from '@/features/licenca/LicencaContext'
import { useAuth } from '@/features/auth/authStore'

export function App() {
  const carregar = useAuth((s) => s.carregar)

  useEffect(() => {
    // Ao arrancar, tenta carregar o utilizador (se houver token na localStorage)
    carregar()
  }, [carregar])

  return (
    <LicencaProvider>
      <RouterProvider router={router} />
    </LicencaProvider>
  )
}