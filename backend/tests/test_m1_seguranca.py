import pytest
from sqlalchemy import text

from app.core.database import SessionLocal


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_sucesso(client):
    r = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin-test-password"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_password_errada(client):
    r = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "errada"},
    )
    assert r.status_code == 401


def test_me_sem_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_com_token(client, auth_headers):
    r = client.get("/api/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "admin"
    assert r.json()["perfil"] == "administrador"


def test_listar_utilizadores_sem_token(client):
    r = client.get("/api/utilizadores")
    assert r.status_code == 401


def test_listar_utilizadores_com_admin(client, auth_headers):
    r = client.get("/api/utilizadores", headers=auth_headers)
    assert r.status_code == 200
    assert any(u["username"] == "admin" for u in r.json())


def test_criar_utilizador(client, auth_headers):
    r = client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "operador1",
            "nome_completo": "Operador Um",
            "perfil": "faturacao",
            "password": "senha-forte-123",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["username"] == "operador1"
    assert r.json()["perfil"] == "faturacao"


def test_criar_utilizador_duplicado(client, auth_headers):
    r = client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "operador1",
            "nome_completo": "Outro",
            "perfil": "auditor",
            "password": "senha-forte-456",
        },
    )
    assert r.status_code == 400


def test_utilizador_nao_admin_nao_gera(client, auth_headers):
    client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "auditor1",
            "nome_completo": "Auditor Um",
            "perfil": "auditor",
            "password": "senha-forte-789",
        },
    )
    r = client.post(
        "/api/auth/login",
        data={"username": "auditor1", "password": "senha-forte-789"},
    )
    assert r.status_code == 200
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r2 = client.get("/api/utilizadores", headers=h)
    assert r2.status_code == 403


def test_bloqueio_apos_tentativas(client, auth_headers):
    client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "bloqueavel",
            "nome_completo": "Bloqueável",
            "perfil": "auditor",
            "password": "senha-forte-000",
        },
    )
    for _ in range(5):
        client.post(
            "/api/auth/login",
            data={"username": "bloqueavel", "password": "errada"},
        )
    r = client.post(
        "/api/auth/login",
        data={"username": "bloqueavel", "password": "senha-forte-000"},
    )
    assert r.status_code == 423


def test_auditoria_append_only(client, admin_token):
    db = SessionLocal()
    try:
        with pytest.raises(Exception):
            db.execute(text("DELETE FROM auditoria"))
            db.commit()
    finally:
        db.rollback()
        db.close()