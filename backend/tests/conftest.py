import os
import subprocess
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

os.environ["SECRET_KEY"] = "test-secret-key-nao-usar-em-producao"
os.environ["INITIAL_ADMIN_USERNAME"] = "admin"
os.environ["INITIAL_ADMIN_PASSWORD"] = "admin-test-password"
os.environ["DATABASE_URL"] = "sqlite:///./test_genesis.db"

# Apagar BD de teste e journals
for _f in ("test_genesis.db", "test_genesis.db-journal"):
    p = BACKEND_DIR / _f
    if p.exists():
        try:
            p.unlink()
        except OSError:
            pass

# Criar schema via Alembic ANTES de importar a app
# (o main.py deixou de usar create_all, agora o schema vem exclusivamente
# do Alembic)
subprocess.run(
    ["alembic", "upgrade", "head"],
    cwd=str(BACKEND_DIR),
    check=True,
    capture_output=True,
    text=True,
    env=os.environ.copy(),
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin-test-password"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}