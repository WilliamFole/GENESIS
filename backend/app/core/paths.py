import sys
from pathlib import Path

# Deteta se está empacotado (.exe) ou a correr em código fonte
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

LOGOS_DIR = UPLOADS_DIR / "logotipos"
LOGOS_DIR.mkdir(parents=True, exist_ok=True)

EXPORTS_DIR = DATA_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

EDECL_DIR = EXPORTS_DIR / "edeclaracao"
EDECL_DIR.mkdir(parents=True, exist_ok=True)

SAFT_DIR = EXPORTS_DIR / "saft"
SAFT_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "genesis.db"