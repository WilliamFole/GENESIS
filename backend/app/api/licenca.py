from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.api.deps import require_perfis
from app.models.utilizador import Perfil, Utilizador
from app.services.licenca import obter_status_licenca, LICENCA_PATH

router = APIRouter(prefix="/api/licenca", tags=["licenca"])


@router.get("/status")
def status_licenca():
    # Rota publica: o ecra de login precisa de saber o estado da licenca
    return obter_status_licenca()


@router.post("/upload")
async def upload_licenca(
    ficheiro: UploadFile = File(...),
    _: Utilizador = Depends(require_perfis(Perfil.ADMINISTRADOR)),
):
    if not ficheiro.filename or not ficheiro.filename.endswith(".lic"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "O ficheiro deve ter extensão .lic")

    conteudo = await ficheiro.read()
    LICENCA_PATH.write_bytes(conteudo)

    status_lic = obter_status_licenca()
    if status_lic["status"] != "ativa":
        LICENCA_PATH.unlink()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Licença inválida ou expirada.")

    return {"ok": True, "detalhes": status_lic}