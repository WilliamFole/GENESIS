from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.api.deps import require_perfis
from app.models.utilizador import Perfil, Utilizador
from app.services import backup

router = APIRouter(prefix="/api/backup", tags=["backup"])

_apenas_admin = require_perfis(Perfil.ADMINISTRADOR)


@router.get("/exportar")
def exportar_backup(
    user: Utilizador = Depends(_apenas_admin),
):
    try:
        conteudo = backup.gerar_backup_zip()
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao gerar backup: {e}")

    nome = f"backup-sge-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return Response(
        conteudo,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@router.post("/importar")
async def importar_backup(
    ficheiro: UploadFile = File(...),
    user: Utilizador = Depends(_apenas_admin),
):
    if not ficheiro.filename or not ficheiro.filename.lower().endswith(".zip"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "O ficheiro deve ser .zip")

    conteudo = await ficheiro.read()
    if not conteudo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ficheiro vazio")

    try:
        manifest = backup.restaurar_backup_zip(conteudo)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao restaurar: {e}")

    return {
        "ok": True,
        "mensagem": "Backup restaurado. Recomenda-se reiniciar o backend.",
        "manifest": manifest,
    }