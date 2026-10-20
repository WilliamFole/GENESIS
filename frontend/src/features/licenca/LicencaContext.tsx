import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

type LicencaStatus = {
  status: 'ativa' | 'expirada' | 'ausente' | 'invalida'
  cliente?: string
  nuit?: string
  validade?: string
}

type LicencaContextType = {
  licenca: LicencaStatus | null
  refresh: () => void
}

const LicencaContext = createContext<LicencaContextType>({
  licenca: null,
  refresh: () => {},
})

export function LicencaProvider({ children }: { children: ReactNode }) {
  // Começa logo com "ausente" para a app não ficar em branco
  const [licenca, setLicenca] = useState<LicencaStatus | null>({
    status: 'ausente',
    cliente: 'Modo de Demonstração',
  })

  const carregar = () => {
    fetch('/api/licenca/status')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) setLicenca(d)
      })
      .catch(() => {
        /* Ignora erros de rede no arranque */
      })
  }

  useEffect(() => {
    carregar()
  }, [])

  // NUNCA coloques um "if (carregando) return ..." aqui. 
  // Deixa o sistema renderizar imediatamente.
  return (
    <LicencaContext.Provider value={{ licenca, refresh: carregar }}>
      {children}
    </LicencaContext.Provider>
  )
}

export const useLicenca = () => useContext(LicencaContext)