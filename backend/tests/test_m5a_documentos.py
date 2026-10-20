from datetime import date, timedelta
from decimal import Decimal


def _criar_contexto(client, auth_headers):
    """Cria (ou reutiliza) serie FT, cliente e artigo para os testes."""

    # Série — idempotente
    r = client.get("/api/series", headers=auth_headers)
    serie_existente = next(
        (s for s in r.json() if s["tipo_documento"] == "FT" and s["prefixo"] == "FTTESTE"),
        None,
    )
    if serie_existente:
        serie_id = serie_existente["id"]
    else:
        r = client.post(
            "/api/series",
            headers=auth_headers,
            json={"tipo_documento": "FT", "prefixo": "FTTESTE"},
        )
        assert r.status_code == 201, r.text
        serie_id = r.json()["id"]

    # Cliente — idempotente
    r = client.get("/api/clientes?q=999000111", headers=auth_headers)
    cliente_existente = next(
        (c for c in r.json() if c["nuit"] == "999000111"), None
    )
    if cliente_existente:
        cliente_id = cliente_existente["id"]
    else:
        r = client.post(
            "/api/clientes",
            headers=auth_headers,
            json={"nuit": "999000111", "nome": "Cliente Teste M5a", "morada": "Rua A"},
        )
        assert r.status_code == 201, r.text
        cliente_id = r.json()["id"]

    # Artigo — idempotente
    r = client.get("/api/artigos?q=SRV-M5A", headers=auth_headers)
    artigo_existente = next(
        (a for a in r.json() if a["codigo"] == "SRV-M5A"), None
    )
    if artigo_existente:
        artigo_id = artigo_existente["id"]
    else:
        r = client.post(
            "/api/artigos",
            headers=auth_headers,
            json={
                "codigo": "SRV-M5A",
                "descricao": "Servico M5a",
                "unidade_id": 9,  # SRV (seed)
                "imposto_id": 1,  # IVA16 (seed)
                "preco_unitario": "116.00",
            },
        )
        assert r.status_code == 201, r.text
        artigo_id = r.json()["id"]

    return serie_id, cliente_id, artigo_id


def test_criar_rascunho(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [
                {"artigo_id": artigo_id, "quantidade": "2", "desconto_percentual": "0"}
            ],
        },
    )
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["estado"] == "rascunho"
    assert doc["numero"] == 0
    # base = 100.00 * 2 = 200.00, iva = 32.00, total = 232.00
    assert Decimal(doc["subtotal"]) == Decimal("200.0000")
    assert Decimal(doc["total_iva"]) == Decimal("32.0000")
    assert Decimal(doc["total"]) == Decimal("232.0000")


def test_editar_rascunho(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]

    r2 = client.patch(
        f"/api/documentos/{doc_id}",
        headers=auth_headers,
        json={"linhas": [{"artigo_id": artigo_id, "quantidade": "5"}]},
    )
    assert r2.status_code == 200
    # base = 500, iva = 80, total = 580
    assert Decimal(r2.json()["subtotal"]) == Decimal("500.0000")
    assert Decimal(r2.json()["total"]) == Decimal("580.0000")


def test_finalizar_documento(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    # Conta o numero de documentos finalizados na serie antes de finalizar
    r_antes = client.get("/api/documentos?tipo=FT&estado=finalizado", headers=auth_headers)
    finais_antes = [d for d in r_antes.json() if d["serie_id"] == serie_id]
    n_antes = len(finais_antes)

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]

    r2 = client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)
    assert r2.status_code == 200, r2.text
    doc = r2.json()
    assert doc["estado"] == "finalizado"
    assert doc["numero"] == n_antes + 1
    assert doc["numero_formatado"] == f"FT FTTESTE/{n_antes + 1}"
    assert doc["finalizado_em"] is not None


def test_tentar_editar_finalizado(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]
    client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)

    r2 = client.patch(
        f"/api/documentos/{doc_id}",
        headers=auth_headers,
        json={"observacoes": "tentativa"},
    )
    assert r2.status_code == 400


def test_tentar_apagar_finalizado(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]
    client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)

    r2 = client.delete(f"/api/documentos/{doc_id}", headers=auth_headers)
    assert r2.status_code == 400


def test_anular_finalizado(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]
    client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)

    r2 = client.post(
        f"/api/documentos/{doc_id}/anular",
        headers=auth_headers,
        json={"motivo_anulacao": "Erro de emissao"},
    )
    assert r2.status_code == 200
    assert r2.json()["estado"] == "anulado"
    assert r2.json()["motivo_anulacao"] == "Erro de emissao"


def test_tentar_editar_anulado(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]
    client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)
    client.post(
        f"/api/documentos/{doc_id}/anular",
        headers=auth_headers,
        json={"motivo_anulacao": "x"},
    )

    r2 = client.patch(
        f"/api/documentos/{doc_id}",
        headers=auth_headers,
        json={"observacoes": "nao devia ser possivel"},
    )
    assert r2.status_code == 400


def test_tentar_anular_rascunho(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]

    r2 = client.post(
        f"/api/documentos/{doc_id}/anular",
        headers=auth_headers,
        json={"motivo_anulacao": "tentativa"},
    )
    assert r2.status_code == 400


def test_numeracao_atomica(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    # Le o ultimo_numero atual da serie
    r_series = client.get("/api/series", headers=auth_headers)
    serie_info = next(s for s in r_series.json() if s["id"] == serie_id)
    n_antes = serie_info["ultimo_numero"]

    docs = []
    for _ in range(2):
        r = client.post(
            "/api/documentos",
            headers=auth_headers,
            json={
                "tipo_documento": "FT",
                "serie_id": serie_id,
                "data_documento": hoje,
                "cliente_id": cliente_id,
                "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
            },
        )
        docs.append(r.json()["id"])

    r1 = client.post(f"/api/documentos/{docs[0]}/finalizar", headers=auth_headers)
    r2 = client.post(f"/api/documentos/{docs[1]}/finalizar", headers=auth_headers)

    assert r1.json()["numero"] == n_antes + 1
    assert r2.json()["numero"] == n_antes + 2


def test_data_anterior_falha(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)

    ontem = (date.today() - timedelta(days=1)).isoformat()
    antes_ontem = (date.today() - timedelta(days=2)).isoformat()

    # Se ja existe algum documento com data > antes_ontem, o teste original nao
    # faz sentido. Garantimos que doc 1 (ontem) e finalizado com sucesso.
    r1 = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": ontem,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    client.post(f"/api/documentos/{r1.json()['id']}/finalizar", headers=auth_headers)

    r2 = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": antes_ontem,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    r3 = client.post(f"/api/documentos/{r2.json()['id']}/finalizar", headers=auth_headers)
    assert r3.status_code == 400


def test_desconto_global(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "desconto_global_percentual": "10",
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    assert r.status_code == 201
    doc = r.json()
    # base 100 -> desconto 10 -> base_final 90, iva 14.4, total 104.4
    assert Decimal(doc["desconto_global_valor"]) == Decimal("10.0000")
    assert Decimal(doc["total_iva"]) == Decimal("14.4000")
    assert Decimal(doc["total"]) == Decimal("104.4000")


def test_desconto_linha(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    r = client.post(
        "/api/documentos",
        headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [
                {
                    "artigo_id": artigo_id,
                    "quantidade": "2",
                    "desconto_percentual": "50",
                }
            ],
        },
    )
    doc = r.json()
    # base 200 -> desconto 100 -> base 100, iva 16, total 116
    assert Decimal(doc["subtotal"]) == Decimal("100.0000")
    assert Decimal(doc["total_iva"]) == Decimal("16.0000")
    assert Decimal(doc["total"]) == Decimal("116.0000")


def test_documento_sem_token(client):
    r = client.get("/api/documentos")
    assert r.status_code == 401


def test_documento_com_faturacao_pode_criar(client, auth_headers):
    serie_id, cliente_id, artigo_id = _criar_contexto(client, auth_headers)
    hoje = date.today().isoformat()

    # cria utilizador faturacao (idempotente)
    client.post(
        "/api/utilizadores",
        headers=auth_headers,
        json={
            "username": "TESTE_FAT_M5A",
            "nome_completo": "TESTE_FAT_M5A",
            "perfil": "faturacao",
            "password": "senha-teste-m5a-forte",
        },
    )
    tok = client.post(
        "/api/auth/login",
        data={"username": "TESTE_FAT_M5A", "password": "senha-teste-m5a-forte"},
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}

    r = client.post(
        "/api/documentos",
        headers=h,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": hoje,
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    assert r.status_code == 201