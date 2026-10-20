import logging
import traceback
from datetime import datetime
from pathlib import Path

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.paths import DATA_DIR

# O ficheiro onde os erros fatais vão ser guardados
LOG_FILE = DATA_DIR / "app_erros.txt"


async def global_exception_handler(request: Request, exc: Exception):
    # 1. Descobre quem estava logado (se disponível)
    user = "Anónimo"
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user.username

    # 2. Constrói o log detalhado
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trace = traceback.format_exc()
    
    log_entry = f"""
==================================================
DATA: {data_hora}
UTILIZADOR: {user}
URL: {request.method} {request.url.path}
ERRO: {exc}
--------------------------------------------------
TRACEBACK:
{trace}
==================================================
"""
    # 3. Grava no ficheiro (append)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass # Se não conseguir gravar o log, não podemos fazer nada.

    # 4. Devolve uma resposta segura ao Frontend
    # (Não mostramos o erro técnico ao utilizador, por segurança)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Ocorreu um erro interno no servidor. A operação foi abortada por segurança.",
            "erro_id": data_hora # Ajuda a encontrar no app_erros.txt
        },
    )