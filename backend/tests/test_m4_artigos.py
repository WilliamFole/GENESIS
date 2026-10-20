from datetime import date, timedelta


# ---------- Unidades ----------


def test_unidades_seed(client, auth_headers):
    r = client.get("/api/unidades", headers=auth_headers)
    assert r.status_code == 200
    codigos = {u["codigo"] for u in r.json()}
    assert {"UN", "KG", "L", "M", "M2", "H", "CX", "PAR", "SRV"} <= codigos


def test_criar_unidade(client, auth_headers):
    r = client.post(
        "/api/unidades",
        headers=auth_headers,
        json={"codigo": "teste_pack", "nome": "TESTE_Pack"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["codigo"] == "TESTE_PACK"


def test_criar_unidade_duplicada(client, auth_headers):
    r = client.post(
        "/api/unidades",
        headers=auth_headers,
        json={"codigo": "TESTE_PACK", "nome": "Duplicada"},
    )
    assert r.status_code == 400


def test_inativar_unidade(client, auth_headers):
    r = client.post(
        "/api/unidades",
        headers=auth_headers,
        json={"codigo": "TESTE_INATIVA", "nome": "TESTE_Inativa"},
    )
    uid = r.json()["id"]

    r2 = client.patch(
        f"/api/unidades/{uid}", headers=auth_headers, json={"ativo": False}
    )
    assert r2.status_code == 200
    assert r2.json()["ativo"] is False


def test_apagar_unidade_em_uso_falha(client, auth_headers):
    # UN ja tem artigos em testes posteriores, mas este teste corre antes.
    # Garantimos que um artigo usa a unidade e tentamos apagar.
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_DEP_UNIDADE",
            "descricao": "Dependencia unidade",
            "unidade_id": 1,  # UN (seed)
            "imposto_id": 1,  # IVA16 (seed)
            "preco_unitario": "100.00",
        },
    )
    assert r.status_code == 201, r.text

    r2 = client.delete("/api/unidades/1", headers=auth_headers)
    assert r2.status_code == 400

    # Limpa o artigo criado para nao interferir com outros testes
    r3 = client.delete(f"/api/artigos/{r.json()['id']}", headers=auth_headers)
    assert r3.status_code == 204


# ---------- Artigos ----------


def test_criar_artigo_valido(client, auth_headers):
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "SRV-CONSULT",
            "descricao": "Consultoria tecnica",
            "unidade_id": 9,  # SRV (seed)
            "imposto_id": 1,  # IVA16
            "preco_unitario": "15000.00",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["codigo"] == "SRV-CONSULT"
    assert r.json()["ativo"] is True


def test_criar_artigo_codigo_duplicado(client, auth_headers):
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "SRV-CONSULT",
            "descricao": "Outra",
            "unidade_id": 1,
            "imposto_id": 1,
            "preco_unitario": "1.00",
        },
    )
    assert r.status_code == 400


def test_criar_artigo_unidade_invalida(client, auth_headers):
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_UNID_INV",
            "descricao": "x",
            "unidade_id": 99999,
            "imposto_id": 1,
            "preco_unitario": "10.00",
        },
    )
    assert r.status_code == 400


def test_criar_artigo_imposto_invalido(client, auth_headers):
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_IMP_INV",
            "descricao": "x",
            "unidade_id": 1,
            "imposto_id": 99999,
            "preco_unitario": "10.00",
        },
    )
    assert r.status_code == 400


def test_criar_artigo_imposto_fora_vigencia(client, auth_headers):
    # Cria imposto com vigencia no futuro
    futuro = (date.today() + timedelta(days=30)).isoformat()
    imp = client.post(
        "/api/impostos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_FUTURO",
            "descricao": "Futuro",
            "tipo": "iva",
            "percentagem": 10,
            "vigencia_inicio": futuro,
        },
    ).json()

    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_ART_FUTURO",
            "descricao": "x",
            "unidade_id": 1,
            "imposto_id": imp["id"],
            "preco_unitario": "10.00",
        },
    )
    assert r.status_code == 400


def test_atualizar_artigo(client, auth_headers):
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_UPDATE",
            "descricao": "Original",
            "unidade_id": 1,
            "imposto_id": 1,
            "preco_unitario": "100.00",
        },
    )
    aid = r.json()["id"]

    r2 = client.patch(
        f"/api/artigos/{aid}",
        headers=auth_headers,
        json={"descricao": "Atualizado", "preco_unitario": "250.00"},
    )
    assert r2.status_code == 200
    assert r2.json()["descricao"] == "Atualizado"
    assert r2.json()["preco_unitario"] == "250.0000"


def test_inativar_artigo(client, auth_headers):
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_INATIVO",
            "descricao": "x",
            "unidade_id": 1,
            "imposto_id": 1,
            "preco_unitario": "10.00",
        },
    )
    aid = r.json()["id"]

    r2 = client.patch(
        f"/api/artigos/{aid}", headers=auth_headers, json={"ativo": False}
    )
    assert r2.status_code == 200
    assert r2.json()["ativo"] is False

    # apenas_ativos exclui este
    r3 = client.get("/api/artigos?apenas_ativos=true", headers=auth_headers)
    assert all(a["id"] != aid for a in r3.json())


def test_apagar_artigo(client, auth_headers):
    r = client.post(
        "/api/artigos",
        headers=auth_headers,
        json={
            "codigo": "TESTE_APAGAR",
            "descricao": "x",
            "unidade_id": 1,
            "imposto_id": 1,
            "preco_unitario": "10.00",
        },
    )
    aid = r.json()["id"]

    r2 = client.delete(f"/api/artigos/{aid}", headers=auth_headers)
    assert r2.status_code == 204

    r3 = client.get(f"/api/artigos/{aid}", headers=auth_headers)
    assert r3.status_code == 404


def test_busca_artigo_por_codigo(client, auth_headers):
    r = client.get("/api/artigos?q=SRV-CONSULT", headers=auth_headers)
    assert r.status_code == 200
    assert any(a["codigo"] == "SRV-CONSULT" for a in r.json())


def test_busca_artigo_por_descricao(client, auth_headers):
    r = client.get("/api/artigos?q=Consultoria", headers=auth_headers)
    assert r.status_code == 200
    assert any("Consultoria" in a["descricao"] for a in r.json())


def test_artigo_sem_token(client):
    r = client.get("/api/artigos")
    assert r.status_code == 401


def test_artigo_com_faturacao_pode_criar(client, auth_headers):
    # cria utilizador faturacao se nao existir (isolamento de M3)
    client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "TESTE_FAT_M4",
            "nome_completo": "TESTE_FAT_M4",
            "perfil": "faturacao",
            "password": "senha-teste-m4-forte",
        },
    )
    tok = client.post(
        "/api/auth/login",
        data={"username": "TESTE_FAT_M4", "password": "senha-teste-m4-forte"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    r = client.post(
        "/api/artigos",
        headers=h,
        json={
            "codigo": "TESTE_FAT_ART",
            "descricao": "x",
            "unidade_id": 1,
            "imposto_id": 1,
            "preco_unitario": "5.00",
        },
    )
    assert r.status_code == 201, r.text