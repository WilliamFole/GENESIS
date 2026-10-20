from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.licenca import obter_status_licenca

ROTAS_LIVRES = [
    "/api/auth/login",
    "/api/auth/recuperar-senha",
    "/api/licenca/upload",
    "/api/licenca/status",       # <-- Garantir que está aqui
    "/api/backup/importar",
]

class LicencaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            if not any(request.url.path.startswith(rota) for rota in ROTAS_LIVRES):
                status_lic = obter_status_licenca()
                if status_lic["status"] != "ativa":
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Licenca expirada ou ausente. Sistema em modo de leitura."}
                    )
        return await call_next(request)