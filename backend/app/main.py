from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import (
    artigos, auth, clientes, auditoria, documentos, empresa, fechos_caixa,
    fiscal, impostos, metodos_pagamento, moedas, pagamentos, relatorios,
    backup, public, recibos, series, unidades, utilizadores, licenca,
)
from app.core.config import settings
from app.core.database import (
    Base, engine, SessionLocal,
    aplicar_triggers_append_only, aplicar_triggers_documentos
)

# ---- IMPORTANTE: Importar todos os modelos para o create_all os encontrar ----
from app.models import artigo  # noqa: F401
from app.models import auditoria as _auditoria  # noqa: F401
from app.models import cliente as _cliente  # noqa: F401
from app.models import documento as _documento  # noqa: F401
from app.models import chave_assinatura as _chave_assinatura  # noqa: F401
from app.models import empresa as _empresa  # noqa: F401
from app.models import fecho_caixa as _fecho_caixa  # noqa: F401
from app.models import ficheiro_exportado as _ficheiro_exportado  # noqa: F401
from app.models import pagamento as _pagamento  # noqa: F401
from app.models import recibo_fatura as _recibo_fatura  # noqa: F401
from app.models import imposto as _imposto  # noqa: F401
from app.models import metodo_pagamento as _metodo_pagamento  # noqa: F401
from app.models import moeda as _moeda  # noqa: F401
from app.models import serie as _serie  # noqa: F401
from app.models import unidade as _unidade  # noqa: F401
from app.models import utilizador as _utilizador  # noqa: F401

from app.services import seed_cadastros, seed_clientes, seed_unidades
from app.services.seed import criar_admin_inicial
from app.middleware.licenca import LicencaMiddleware
from app.api.auth import gerar_codigo_recuperacao
from app.core.error_handler import global_exception_handler


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LicencaMiddleware)

# ---- Base de Dados e Triggers ----
print("A verificar a base de dados...")
Base.metadata.create_all(bind=engine)
aplicar_triggers_append_only()
aplicar_triggers_documentos()

# ---- Seeds ----
print("A inicializar dados base...")
with SessionLocal() as _db:
    criar_admin_inicial(_db)
    seed_cadastros.executar(_db)
    seed_clientes.executar(_db)
    seed_unidades.executar(_db)
    gerar_codigo_recuperacao()

# ---- Rotas ----
app.include_router(licenca.router)
app.include_router(auth.router)
app.include_router(utilizadores.router)
app.include_router(empresa.router)
app.include_router(impostos.router)
app.include_router(moedas.router)
app.include_router(series.router)
app.include_router(metodos_pagamento.router)
app.include_router(clientes.router)
app.include_router(unidades.router)
app.include_router(artigos.router)
app.include_router(documentos.router)
app.include_router(public.router)
app.include_router(fiscal.router)
app.include_router(pagamentos.router)
app.include_router(recibos.router)
app.include_router(fechos_caixa.router)
app.include_router(relatorios.router)
app.include_router(auditoria.router)
app.include_router(backup.router)

@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}

# ---- Frontend ----
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend_dist"
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def servir_react(full_path: str):
        if full_path.startswith("api/"):
            return {"detail": "Not Found"}
        ficheiro = FRONTEND_DIR / full_path
        if ficheiro.exists() and ficheiro.is_file():
            return FileResponse(ficheiro)
        return FileResponse(FRONTEND_DIR / "index.html")