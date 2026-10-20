from datetime import date


def test_empresa_ausente_retorna_null(client, auth_headers):
    r = client.get("/api/empresa", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() is None


def test_criar_empresa(client, auth_headers):
    r = client.put(
        "/api/empresa",
        headers=auth_headers,
        json={
            "nuit": "000000000",
            "designacao": "TESTE_EMITENTE",
            "morada": "TESTE_MORADA",
            "regime_iva": "geral",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["nuit"] == "000000000"
    assert r.json()["designacao"] == "TESTE_EMITENTE"


def test_upsert_empresa_atualiza(client, auth_headers):
    r = client.put(
        "/api/empresa",
        headers=auth_headers,
        json={
            "nuit": "000000000",
            "designacao": "TESTE_EMITENTE_V2",
            "morada": "TESTE_MORADA",
            "regime_iva": "geral",
        },
    )
    assert r.status_code == 200
    assert r.json()["designacao"] == "TESTE_EMITENTE_V2"


def test_empresa_requer_admin(client, auth_headers):
    r = client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "TESTE_FAT_M2",
            "nome_completo": "TESTE_FAT_M2",
            "perfil": "faturacao",
            "password": "senha-teste-m2-forte",
        },
    )
    assert r.status_code == 201, r.text

    tok = client.post(
        "/api/auth/login",
        data={"username": "TESTE_FAT_M2", "password": "senha-teste-m2-forte"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    r = client.put(
        "/api/empresa",
        headers=h,
        json={
            "nuit": "111111111",
            "designacao": "X",
            "morada": "Y",
            "regime_iva": "geral",
        },
    )
    assert r.status_code == 403


def test_listar_impostos_seed(client, auth_headers):
    r = client.get("/api/impostos", headers=auth_headers)
    assert r.status_code == 200
    codigos = {i["codigo"] for i in r.json()}
    assert {"IVA16", "IVA0", "ISE"} <= codigos


def test_criar_imposto_isento_sem_motivo_falha(client, auth_headers):
    r = client.post(
        "/api/impostos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_ISE",
            "descricao": "TESTE_ISE",
            "tipo": "isento",
            "percentagem": 0,
            "vigencia_inicio": date.today().isoformat(),
        },
    )
    assert r.status_code == 422


def test_criar_imposto_valido(client, auth_headers):
    r = client.post(
        "/api/impostos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_IVA5",
            "descricao": "TESTE_IVA5",
            "tipo": "iva",
            "percentagem": 5,
            "vigencia_inicio": date.today().isoformat(),
        },
    )
    assert r.status_code == 201, r.text


def test_listar_moedas_seed(client, auth_headers):
    r = client.get("/api/moedas", headers=auth_headers)
    assert r.status_code == 200
    base = [m for m in r.json() if m["base"]]
    assert len(base) == 1
    assert base[0]["codigo"] == "MZN"


def test_criar_moeda(client, auth_headers):
    r = client.post(
        "/api/moedas",
        headers=auth_headers,
        json={"codigo": "USD", "nome": "TESTE_USD"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["codigo"] == "USD"
    assert r.json()["base"] is False


def test_moeda_base_nao_pode_ser_desativada(client, auth_headers):
    r = client.get("/api/moedas", headers=auth_headers)
    mzn_id = next(m["id"] for m in r.json() if m["codigo"] == "MZN")
    r2 = client.patch(f"/api/moedas/{mzn_id}", headers=auth_headers, json={"ativo": False})
    assert r2.status_code == 400


def test_listar_metodos_pagamento_seed(client, auth_headers):
    r = client.get("/api/metodos-pagamento", headers=auth_headers)
    assert r.status_code == 200
    codigos = {m["codigo"] for m in r.json()}
    assert {"NUM", "TRF", "CAR", "MPESA", "EMOLA", "CHQ"} <= codigos


def test_serie_fechada_nao_reabre(client, auth_headers):
    r = client.post(
        "/api/series",
        headers=auth_headers,
        json={"tipo_documento": "FT", "prefixo": "TESTE_FT2026"},
    )
    assert r.status_code == 201, r.text
    sid = r.json()["id"]

    r2 = client.patch(f"/api/series/{sid}", headers=auth_headers, json={"ativo": False})
    assert r2.status_code == 200

    r3 = client.patch(f"/api/series/{sid}", headers=auth_headers, json={"ativo": True})
    assert r3.status_code == 400


def test_serie_duplicada(client, auth_headers):
    client.post(
        "/api/series",
        headers=auth_headers,
        json={"tipo_documento": "VD", "prefixo": "TESTE_VD2026"},
    )
    r = client.post(
        "/api/series",
        headers=auth_headers,
        json={"tipo_documento": "VD", "prefixo": "TESTE_VD2026"},
    )
    assert r.status_code == 400


def test_upload_logotipo(client, auth_headers):
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    r = client.post(
        "/api/empresa/logotipo",
        headers=auth_headers,
        files={"file": ("logo.png", png, "image/png")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["logotipo_path"]

    r2 = client.get("/api/empresa/logotipo", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.content == png


def test_upload_logotipo_tipo_invalido(client, auth_headers):
    r = client.post(
        "/api/empresa/logotipo",
        headers=auth_headers,
        files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert r.status_code == 400


def test_auditoria_registou_operacoes_m2(client, auth_headers):
    from sqlalchemy import text
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        total = db.execute(text("SELECT COUNT(*) FROM auditoria")).scalar()
        assert total > 0
    finally:
        db.close()