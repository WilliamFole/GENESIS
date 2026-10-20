def test_listar_clientes_inclui_consumidor_final(client, auth_headers):
    r = client.get("/api/clientes", headers=auth_headers)
    assert r.status_code == 200
    dados = r.json()
    cf = [c for c in dados if c["consumidor_final"]]
    assert len(cf) == 1
    assert cf[0]["nuit"] == "999999999"
    assert cf[0]["nome"] == "Consumidor final"


def test_criar_cliente_valido(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={
            "nuit": "111222333",
            "nome": "TESTE_CLIENTE_1",
            "morada": "TESTE_MORADA_1",
            "telefone": "840000000",
            "email": "teste1@exemplo.mz",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["nuit"] == "111222333"
    assert r.json()["ativo"] is True
    assert r.json()["consumidor_final"] is False


def test_criar_cliente_nuit_invalido(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={
            "nuit": "12345",
            "nome": "TESTE_NUIT_CURTO",
            "morada": "TESTE_MORADA",
        },
    )
    assert r.status_code == 422


def test_criar_cliente_nuit_com_letras(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={
            "nuit": "12345ABCD",
            "nome": "TESTE_NUIT_LETRAS",
            "morada": "TESTE_MORADA",
        },
    )
    assert r.status_code == 422


def test_criar_cliente_nuit_duplicado(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={
            "nuit": "111222333",
            "nome": "TESTE_DUPLICADO",
            "morada": "TESTE_MORADA",
        },
    )
    assert r.status_code == 400


def test_criar_cliente_nuit_igual_ao_consumidor_final(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={
            "nuit": "999999999",
            "nome": "TESTE_CONFLITO_CF",
            "morada": "TESTE_MORADA",
        },
    )
    assert r.status_code == 400


def test_editar_cliente(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={
            "nuit": "222333444",
            "nome": "TESTE_CLIENTE_EDIT",
            "morada": "TESTE_MORADA_EDIT",
        },
    )
    assert r.status_code == 201
    cid = r.json()["id"]

    r2 = client.patch(
        f"/api/clientes/{cid}",
        headers=auth_headers,
        json={"nome": "TESTE_CLIENTE_EDIT_V2", "telefone": "850000000"},
    )
    assert r2.status_code == 200
    assert r2.json()["nome"] == "TESTE_CLIENTE_EDIT_V2"
    assert r2.json()["telefone"] == "850000000"


def test_editar_nuit_duplicado_falha(client, auth_headers):
    # cria cliente A e B
    ra = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={"nuit": "333444555", "nome": "A", "morada": "M"},
    ).json()
    rb = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={"nuit": "444555666", "nome": "B", "morada": "M"},
    ).json()

    r = client.patch(
        f"/api/clientes/{rb['id']}",
        headers=auth_headers,
        json={"nuit": ra["nuit"]},
    )
    assert r.status_code == 400


def test_inativar_cliente(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={"nuit": "555666777", "nome": "TESTE_INATIVAR", "morada": "M"},
    )
    cid = r.json()["id"]

    r2 = client.patch(
        f"/api/clientes/{cid}",
        headers=auth_headers,
        json={"ativo": False},
    )
    assert r2.status_code == 200
    assert r2.json()["ativo"] is False

    # listar apenas ativos nao inclui este
    r3 = client.get("/api/clientes?apenas_ativos=true", headers=auth_headers)
    assert all(c["id"] != cid for c in r3.json())


def test_apagar_cliente_sem_documentos(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={"nuit": "666777888", "nome": "TESTE_APAGAR", "morada": "M"},
    )
    cid = r.json()["id"]

    r2 = client.delete(f"/api/clientes/{cid}", headers=auth_headers)
    assert r2.status_code == 204

    r3 = client.get(f"/api/clientes/{cid}", headers=auth_headers)
    assert r3.status_code == 404


def test_consumidor_final_nao_pode_ser_apagado(client, auth_headers):
    r = client.get("/api/clientes", headers=auth_headers)
    cf = next(c for c in r.json() if c["consumidor_final"])
    r2 = client.delete(f"/api/clientes/{cf['id']}", headers=auth_headers)
    assert r2.status_code == 400


def test_consumidor_final_nao_permite_editar_nome(client, auth_headers):
    r = client.get("/api/clientes", headers=auth_headers)
    cf = next(c for c in r.json() if c["consumidor_final"])
    r2 = client.patch(
        f"/api/clientes/{cf['id']}",
        headers=auth_headers,
        json={"nome": "OUTRO NOME"},
    )
    assert r2.status_code == 400


def test_conta_corrente_vazia(client, auth_headers):
    r = client.post(
        "/api/clientes",
        headers=auth_headers,
        json={"nuit": "777888999", "nome": "TESTE_CC", "morada": "M"},
    )
    cid = r.json()["id"]

    r2 = client.get(f"/api/clientes/{cid}/conta-corrente", headers=auth_headers)
    assert r2.status_code == 200
    dados = r2.json()
    assert dados["saldo"] == "0"
    assert dados["movimentos"] == []
    assert dados["cliente_id"] == cid


def test_conta_corrente_cliente_inexistente(client, auth_headers):
    r = client.get("/api/clientes/999999/conta-corrente", headers=auth_headers)
    assert r.status_code == 404


def test_busca_por_nome(client, auth_headers):
    client.post(
        "/api/clientes",
        headers=auth_headers,
        json={"nuit": "888999111", "nome": "TESTE_BUSCA_ABC", "morada": "M"},
    )
    r = client.get("/api/clientes?q=BUSCA_ABC", headers=auth_headers)
    assert r.status_code == 200
    nomes = [c["nome"] for c in r.json()]
    assert "TESTE_BUSCA_ABC" in nomes


def test_busca_por_nuit(client, auth_headers):
    r = client.get("/api/clientes?q=888999111", headers=auth_headers)
    assert r.status_code == 200
    assert any(c["nuit"] == "888999111" for c in r.json())


def test_cliente_sem_token(client):
    r = client.get("/api/clientes")
    assert r.status_code == 401


def test_cliente_com_faturacao_pode_criar(client, auth_headers):
    # criar utilizador com perfil faturacao
    r = client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "TESTE_FAT_M3",
            "nome_completo": "TESTE_FAT_M3",
            "perfil": "faturacao",
            "password": "senha-teste-m3-forte",
        },
    )
    assert r.status_code == 201, r.text

    tok = client.post(
        "/api/auth/login",
        data={"username": "TESTE_FAT_M3", "password": "senha-teste-m3-forte"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    r2 = client.post(
        "/api/clientes",
        headers=h,
        json={"nuit": "101010101", "nome": "TESTE_FAT_CRIA", "morada": "M"},
    )
    assert r2.status_code == 201, r2.text