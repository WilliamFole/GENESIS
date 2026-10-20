import { create } from 'zustand'
import { api, setToken } from '@/lib/api'

export type Perfil = 'administrador' | 'faturacao' | 'contabilista' | 'auditor'

export type Utilizador = {
  id: number
  username: string
  nome_completo: string
  perfil: Perfil
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

type AuthState = {
  user: Utilizador | null
  carregado: boolean
  login: (token: string) => Promise<void>
  logout: () => void
  carregar: () => Promise<void>
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  carregado: false,
  login: async (token) => {
    setToken(token)
    const user = await api<Utilizador>('/api/auth/me')
    set({ user, carregado: true })
  },
  logout: () => {
    setToken(null)
    set({ user: null, carregado: true })
  },
  carregar: async () => {
    try {
      const user = await api<Utilizador>('/api/auth/me')
      set({ user, carregado: true })
    } catch {
      set({ user: null, carregado: true })
    }
  },
}))