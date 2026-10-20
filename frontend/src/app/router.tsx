import { createBrowserRouter, Navigate } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LoginPage } from '@/features/auth/LoginPage'
import { ClientesPage } from '@/features/clientes/ClientesPage'
import { UtilizadoresPage } from '@/features/utilizadores/UtilizadoresPage'
import { EmpresaPage } from '@/features/configuracao/EmpresaPage'
import { ImpostosPage } from '@/features/configuracao/ImpostosPage'
import { MoedasPage } from '@/features/configuracao/MoedasPage'
import { SeriesPage } from '@/features/configuracao/SeriesPage'
import { MetodosPagamentoPage } from '@/features/configuracao/MetodosPagamentoPage'
import { ArtigosPage } from '@/features/artigos/ArtigosPage'
import { UnidadesPage } from '@/features/artigos/UnidadesPage'
import { FaturasPage } from '@/features/vendas/FaturasPage'
import { NovaFaturaPage } from '@/features/vendas/NovaFaturaPage'
import { VerificarPage } from '@/features/public/VerificarPage'
import { FiscalPage } from '@/features/fiscal/FiscalPage'
import { PagamentosPage } from '@/features/pagamentos/PagamentosPage'
import { FechosCaixaPage } from '@/features/fechos-caixa/FechosCaixaPage'
import { RecibosPage } from '@/features/vendas/RecibosPage'
import { NovaNotaPage } from '@/features/vendas/NovaNotaPage'
import { ListaDocumentosPage } from '@/features/vendas/ListaDocumentosPage'
import { RelatoriosPage } from '@/features/relatorios/RelatoriosPage'
import { RelatoriosVendasPage } from '@/features/relatorios/RelatoriosVendasPage'
import { RelatoriosDocumentosPage } from '@/features/relatorios/RelatoriosDocumentosPage'
import { RelatoriosNumeracaoPage } from '@/features/relatorios/RelatoriosNumeracaoPage'
import { RelatoriosSaldosPage } from '@/features/relatorios/RelatoriosSaldosPage'
import { RelatoriosExtratoClientePage } from '@/features/relatorios/RelatoriosExtratoClientePage'
import { AuditoriaPage } from '@/features/auditoria/AuditoriaPage'
import { BackupPage } from '@/features/ferramentas/BackupPage'
import { LicencaPage } from '@/features/licenca/LicencaPage'

function Placeholder({ titulo, nota }: { titulo: string; nota?: string }) {
  return (
    <div>
      <h1 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#1F5BA8' }}>{titulo}</h1>
      <p style={{ fontSize: 13, color: '#44546A', marginTop: 8 }}>{nota ?? 'Módulo ainda não implementado.'}</p>
    </div>
  )
}

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/v/:codigo', element: <VerificarPage /> },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: null },
      { path: 'ficheiro/sobre', element: <Placeholder titulo="Sobre o Genesis" /> },

      // ---- Base ----
      { path: 'base', element: <Navigate to="/base/clientes" replace /> },
      { path: 'base/clientes', element: <ClientesPage /> },
      { path: 'base/artigos', element: <ArtigosPage /> },
      { path: 'base/unidades', element: <ProtectedRoute perfis={['administrador']}><UnidadesPage /></ProtectedRoute> },
      { path: 'base/empresa', element: <ProtectedRoute perfis={['administrador']}><EmpresaPage /></ProtectedRoute> },
      { path: 'base/impostos', element: <ProtectedRoute perfis={['administrador']}><ImpostosPage /></ProtectedRoute> },
      { path: 'base/moedas', element: <ProtectedRoute perfis={['administrador']}><MoedasPage /></ProtectedRoute> },
      { path: 'base/series', element: <ProtectedRoute perfis={['administrador']}><SeriesPage /></ProtectedRoute> },
      { path: 'base/metodos-pagamento', element: <ProtectedRoute perfis={['administrador']}><MetodosPagamentoPage /></ProtectedRoute> },

      // ---- Vendas ----
      { path: 'vendas', element: <Navigate to="/vendas/faturas" replace /> },
      { path: 'vendas/faturas', element: <FaturasPage /> },
      { path: 'vendas/faturas/nova', element: <NovaFaturaPage /> },
      { path: 'vendas/faturas/:id', element: <NovaFaturaPage /> },
      { path: 'vendas/faturas-recibo', element: <ListaDocumentosPage titulo="Faturas-Recibo (FS)" tipos={['FS']} linkNovo="/vendas/faturas/nova" /> },
      { path: 'vendas/notas-credito', element: <ListaDocumentosPage titulo="Notas de Crédito (NC)" tipos={['NC']} linkNovo="/vendas/notas-credito/nova" /> },
      { path: 'vendas/notas-credito/nova', element: <NovaNotaPage tipo="NC" /> },      
      { path: 'vendas/notas-debito', element: <ListaDocumentosPage titulo="Notas de Débito (ND)" tipos={['ND']} linkNovo="/vendas/notas-debito/nova" /> },
      { path: 'vendas/notas-debito/nova', element: <NovaNotaPage tipo="ND" /> },
      { path: 'vendas/nao-fiscais', element: <ListaDocumentosPage titulo="Documentos Não Fiscais" tipos={['COT', 'PRO', 'GR']} linkNovo="/vendas/faturas/nova" /> },
      { path: 'vendas/recibos', element: <RecibosPage /> },

      // ---- Stocks ----
      { path: 'stocks', element: <Navigate to="/stocks/inventario" replace /> },
      { path: 'stocks/inventario', element: <Placeholder titulo="Controlo de stock" nota="Fora do primeiro lote." /> },

      // ---- Tesouraria ----
      { path: 'tesouraria', element: <Navigate to="/tesouraria/pagamentos" replace /> },
      { path: 'tesouraria/pagamentos', element: <PagamentosPage /> },
      { path: 'tesouraria/fechos-caixa', element: <FechosCaixaPage /> },

      // ---- Relatórios ----
      { path: 'relatorios', element: <Navigate to="/relatorios/vendas" replace /> },
      { path: 'relatorios/vendas', element: <RelatoriosVendasPage /> },
      { path: 'relatorios/documentos', element: <RelatoriosDocumentosPage /> },
      { path: 'relatorios/numeracao', element: <RelatoriosNumeracaoPage /> },
      { path: 'relatorios/saldos', element: <RelatoriosSaldosPage /> },
      { path: 'relatorios/extrato-cliente', element: <RelatoriosExtratoClientePage /> },
      { path: 'relatorios/auditoria-numeracao', element: <RelatoriosPage /> },
      { path: 'relatorios/fiscal', element: <FiscalPage /> },

      // ---- Ferramentas (Rotas Corrigidas) ----
      { path: 'ferramentas', element: <Navigate to="/ferramentas/utilizadores" replace /> },
      { path: 'ferramentas/utilizadores', element: <ProtectedRoute perfis={['administrador']}><UtilizadoresPage /></ProtectedRoute> },
      { path: 'ferramentas/auditoria', element: <ProtectedRoute perfis={['administrador', 'auditor']}><AuditoriaPage /></ProtectedRoute> },
      { path: 'ferramentas/backup', element: <BackupPage /> },
      { path: 'ferramentas/licenca', element: <LicencaPage /> },

      // ---- Redirects ----
      { path: 'clientes', element: <Navigate to="/base/clientes" replace /> },
      { path: 'configuracao', element: <Navigate to="/base/empresa" replace /> },
      { path: 'configuracao/*', element: <Navigate to="/base/empresa" replace /> },
      { path: 'utilizadores', element: <Navigate to="/ferramentas/utilizadores" replace /> },
      { path: 'auditoria', element: <Navigate to="/ferramentas/auditoria" replace /> },
      { path: 'faturacao', element: <Navigate to="/vendas/faturas" replace /> },
      { path: 'artigos', element: <Navigate to="/base/artigos" replace /> },
      { path: 'pagamentos', element: <Navigate to="/tesouraria/pagamentos" replace /> },
      { path: 'fiscal', element: <Navigate to="/relatorios/fiscal" replace /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])