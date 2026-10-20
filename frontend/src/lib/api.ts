const TOKEN_KEY = 'genesis.token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}

export async function api<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(endpoint, { ...options, headers })

  if (res.status === 403) {
    const clone = res.clone()
    try {
      const data = await clone.json()
      if (data.detail && data.detail.includes('Licenca')) {
        alert('A sua licença expirou ou é inválida. O sistema está em modo de leitura. Por favor, contacte o fornecedor para renovar.')
        throw new Error('Licença expirada')
      }
    } catch (e) {
      // Ignorar se não for JSON
    }
  }

  if (!res.ok) {
    const txt = await res.text()
    let msg = txt
    try {
      const j = JSON.parse(txt)
      if (j.detail) msg = j.detail
    } catch {}
    throw new Error(msg || `HTTP ${res.status}`)
  }

  if (res.status === 204) return null as T
  return res.json()
}
export async function login(username: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username, password })
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })
  if (!res.ok) {
    let detalhe = 'Credenciais inválidas'
    try {
      const data = await res.json()
      detalhe = data?.detail ?? detalhe
    } catch {
      /* ignorar */
    }
    throw new Error(detalhe)
  }
  const data = (await res.json()) as { access_token: string }
  return data.access_token
}