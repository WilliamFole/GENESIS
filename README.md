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
   git clone https://github.com/WilliamFole/GENESIS.git
   cd GENESIS
   ```

2. Backend (Python 3.12):
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
   pip install -r requirements.txt
   pip install -r requirements-dev.txt   # só para correr os testes
   alembic upgrade head
   python -m uvicorn app.main:app --port 8000
   ```

3. Frontend (Node 18+), noutro terminal:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Abre http://localhost:5173 (o frontend encaminha `/api` para a porta 8000).

## 🔐 Configuração e segurança

Antes de usar em produção, cria o ficheiro `backend/.env` (nunca o envies para o GitHub):

```env
SECRET_KEY=<texto-aleatorio-longo>
INITIAL_ADMIN_PASSWORD=<palavra-passe-forte>
```

- `SECRET_KEY` também protege as chaves de assinatura RSA guardadas na base de dados. **Define-a antes da primeira utilização e não a mudes depois**, senão as chaves existentes deixam de poder ser lidas.
- Troca a palavra-passe do administrador no primeiro login.
- Para o sistema recusar arrancar com a configuração insegura, define `GENESIS_STRICT_SECURITY=1`.

## 🧪 Testes

```bash
cd backend
python -m pytest -q
```
