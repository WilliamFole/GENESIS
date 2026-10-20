import type { Perfil } from '@/features/auth/authStore'

export type MenuItem = {
  label: string
  path?: string
  action?: 'logout'
  perfis?: Perfil[]
}

export type MenuSection = {
  label: string
  items: MenuItem[]
}

export type MenuGroup = {
  id: string
  label: string
  basePath: string
  sections: MenuSection[]
}

export const MENUS: MenuGroup[] = [
  {
    id: 'ficheiro',
    label: 'Ficheiro',
    basePath: '/ficheiro',
    sections: [
      {
        label: 'Sessão',
        items: [
          { label: 'Sobre', path: '/ficheiro/sobre' },
          { label: 'Sair', action: 'logout' },
        ],
      },
    ],
  },
  {
    id: 'base',
    label: 'Base',
    basePath: '/base',
    sections: [
      {
        label: 'Cadastros',
        items: [
          { label: 'Clientes', path: '/base/clientes' },
          { label: 'Artigos e serviços', path: '/base/artigos' },
        ],
      },
      {
        label: 'Configuração',
        items: [
          { label: 'Emitente', path: '/base/empresa', perfis: ['administrador'] },
          { label: 'Impostos', path: '/base/impostos', perfis: ['administrador'] },
          { label: 'Moedas', path: '/base/moedas', perfis: ['administrador'] },
          { label: 'Séries', path: '/base/series', perfis: ['administrador'] },
          { label: 'Métodos de pagamento', path: '/base/metodos-pagamento', perfis: ['administrador'] },
          { label: 'Unidades', path: '/base/unidades', perfis: ['administrador'] },
        ],
      },
    ],
  },
  {
    id: 'vendas',
    label: 'Vendas',
    basePath: '/vendas',
    sections: [
      {
        label: 'Documentos',
        items: [
          { label: 'Faturas', path: '/vendas/faturas' },
          { label: 'Faturas-recibo', path: '/vendas/faturas-recibo' },
          { label: 'Notas de crédito', path: '/vendas/notas-credito' },
          { label: 'Documentos Não Fiscais', path: '/vendas/nao-fiscais' },
          { label: 'Notas de débito', path: '/vendas/notas-debito' },
          { label: 'Recibos', path: '/vendas/recibos' },
        ],
      },
    ],
  },
  {
    id: 'stocks',
    label: 'Stocks',
    basePath: '/stocks',
    sections: [
      {
        label: 'Inventário',
        items: [{ label: 'Controlo de stock (v2)', path: '/stocks/inventario' }],
      },
    ],
  },
  {
    id: 'tesouraria',
    label: 'Tesouraria',
    basePath: '/tesouraria',
    sections: [
      {
        label: 'Tesouraria',
        items: [
          { label: 'Pagamentos', path: '/tesouraria/pagamentos' },
          { label: 'Fechos de caixa', path: '/tesouraria/fechos-caixa' },
        ],
      },
    ],
  },
  {
    id: 'relatorios',
    label: 'Relatórios',
    basePath: '/relatorios',
    sections: [
      {
        label: 'Relatórios',
        items: [
          { label: 'Vendas', path: '/relatorios/vendas' },
          { label: 'Documentos', path: '/relatorios/documentos' },
          { label: 'Numeração', path: '/relatorios/numeracao' },
          { label: 'Saldos', path: '/relatorios/saldos' },
          { label: 'Extrato Cliente', path: '/relatorios/extrato-cliente' },
          { label: 'Fiscal e exportação', path: '/relatorios/fiscal' },
        ],
      },
    ],
  },
  {
    id: 'ferramentas',
    label: 'Ferramentas',
    basePath: '/ferramentas',
    sections: [
      {
        label: 'Gestão do Sistema',
        items: [
          { label: 'Utilizadores', path: '/ferramentas/utilizadores', perfis: ['administrador'] },
          { label: 'Auditoria', path: '/ferramentas/auditoria', perfis: ['administrador', 'auditor'] },
          { label: 'Backup / Restauro', path: '/ferramentas/backup' },
          { label: 'Gestão de Licença', path: '/ferramentas/licenca' },
        ],
      },
    ],
  },
]

export function findMenuGroup(pathname: string): MenuGroup | null {
  for (const m of MENUS) {
    if (pathname === m.basePath || pathname.startsWith(m.basePath + '/')) return m
  }
  return null
}

export function findMenuItem(pathname: string): MenuItem | null {
  for (const g of MENUS) {
    for (const s of g.sections) {
      for (const i of s.items) {
        if (i.path === pathname) return i
      }
    }
  }
  return null
}

export function firstItemPath(group: MenuGroup): string | null {
  for (const s of group.sections) {
    for (const i of s.items) {
      if (i.path) return i.path
    }
  }
  return null
}