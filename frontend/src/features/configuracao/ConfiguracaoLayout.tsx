import { NavLink, Outlet } from 'react-router-dom'

const tabs = [
  { to: 'empresa', label: 'Emitente' },
  { to: 'impostos', label: 'Impostos' },
  { to: 'moedas', label: 'Moedas' },
  { to: 'series', label: 'Séries' },
  { to: 'metodos-pagamento', label: 'Métodos de pagamento' },
]

export function ConfiguracaoLayout() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">Configuração</h1>
      <div className="border-b border-slate-200 mb-6 flex gap-2 flex-wrap">
        {tabs.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) =>
              `px-3 py-2 text-sm border-b-2 -mb-px ${
                isActive
                  ? 'border-slate-900 text-slate-900 font-medium'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`
            }
          >
            {t.label}
          </NavLink>
        ))}
      </div>
      <Outlet />
    </div>
  )
}