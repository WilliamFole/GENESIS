import io
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_DIR / "genesis.db"
UPLOADS_DIR = BACKEND_DIR / "uploads"


def gerar_backup_zip() -> bytes:
    """Gera um zip com a BD, uploads/ e um manifest.json."""
    if not DB_PATH.exists():
        raise FileNotFoundError("Base de dados genesis.db nao encontrada.")

    buf = io.BytesIO()

    # Copia segura da BD (evita bloquear)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp_db_path = tmp.name

    try:
        src = sqlite3.connect(str(DB_PATH))
        dst = sqlite3.connect(tmp_db_path)
        with dst:
            src.backup(dst)
        src.close()
        dst.close()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # BD
            zf.write(tmp_db_path, "genesis.db")

            # Uploads (logos, pdfs, etc.)
            if UPLOADS_DIR.exists():
                for root, _, files in os.walk(UPLOADS_DIR):
                    for f in files:
                        full = Path(root) / f
                        rel = full.relative_to(BACKEND_DIR)
                        zf.write(full, str(rel))

            # Manifest
            manifest = {
                "gerado_em": datetime.utcnow().isoformat(),
                "versao": "1.0",
                "empresa": settings.DATABASE_URL.split("sqlite:///")[-1],
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

    finally:
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)

    return buf.getvalue()


def restaurar_backup_zip(conteudo: bytes) -> dict:
    """Restaura a BD e os uploads a partir do zip. Devolve info do manifest."""
    buf = io.BytesIO(conteudo)
    if not zipfile.is_zipfile(buf):
        raise ValueError("Ficheiro invalido. Nao e um zip.")
    buf.seek(0)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        with zipfile.ZipFile(buf) as zf:
            # Verifica se tem os elementos mínimos
            names = zf.namelist()
            if "genesis.db" not in names:
                raise ValueError("Backup invalido: genesis.db em falta.")

            # Lê manifest
            manifest = {}
            if "manifest.json" in names:
                manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

            # Extrai tudo para tmpdir
            zf.extractall(tmpdir_path)

        # Substitui a BD (fecha qualquer conexão aberta antes de substituir)
        novo_db = tmpdir_path / "genesis.db"
        if DB_PATH.exists():
            shutil.copy2(DB_PATH, DB_PATH.with_suffix(".db.bak"))
        shutil.copy2(novo_db, DB_PATH)

        # Substitui uploads (preserva o antigo como .bak)
        novo_uploads = tmpdir_path / "uploads"
        if novo_uploads.exists():
            if UPLOADS_DIR.exists():
                shutil.make_archive(str(UPLOADS_DIR) + "_bak", "zip", UPLOADS_DIR)
                shutil.rmtree(UPLOADS_DIR)
            shutil.copytree(novo_uploads, UPLOADS_DIR)

    return manifest