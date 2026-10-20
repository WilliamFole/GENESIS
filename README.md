# SGE - Sistema de Gestão Empresarial e Faturação

Software de faturação certificável para a República de Moçambique. Funciona 100% offline (local-first), com suporte a SAF-T e e-Declaração.

## 🚀 Funcionalidades
- Emissão de Faturas (FT), Vendas a Dinheiro (VD), Faturas Simplificadas (FS), Notas de Crédito (NC) e Débito (ND).
- Emissão de Recibos (RC) e Fecho de Caixa.
- Assinatura digital RSA e Hash encadeado para integridade fiscal.
- Relatórios de Vendas, Extratos de Clientes, Mapa de IVA.
- Exportação SAF-T e e-Declaração (Aviso 40/AT).
- Sistema de Licenciamento por empresa (geração de `.lic` com chave RSA).

## 🛠️ Tecnologias
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, SQLite.
- **Frontend:** React, TypeScript, Vite, TailwindCSS.
- **Empacotamento:** PyInstaller (backend) + Inno Setup (instalador Windows).

## 📦 Como instalar (Desenvolvimento)

1. Clona o repositório:
   ```bash
   git clone https://github.com/SEU_USUARIO/genesis-sge.git
   cd genesis-sge