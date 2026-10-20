from datetime import date
from decimal import Decimal


def _obter_ou_criar_serie(client, auth_headers, tipo, prefixo):
    r = client.get("/api/series", headers=auth_headers)
    existente = next(
        (s for s in r.json() if s["tipo_documento"] == tipo and s["prefixo"] == prefixo),
        None,
    )
    if existente:
        return existente["id"]
    r = client.post(
        "/api/series", headers=auth_headers,
        json={"tipo_documento": tipo, "prefixo": prefixo},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _criar_contexto(client, auth_headers):
    ctx = {
        "serie_ft": _obter_ou_criar_serie(client, auth_headers, "FT", "M5CFT"),
        "serie_nc": _obter_ou_criar_serie(client, auth_headers, "NC", "M5CNC"),
        "serie_nd": _obter_ou_criar_serie(client, auth_headers, "ND", "M5CND"),
        "serie_fs": _obter_ou_criar_serie(client, auth_headers, "FS", "M5CFS"),
        "serie_cot": _obter_ou_criar_serie(client, auth_headers, "COT", "M5CCOT"),
        "serie_pro": _obter_ou_criar_serie(client, auth_headers, "PRO", "M5CPRO"),
        "serie_gr": _obter_ou_criar_serie(client, auth_headers, "GR", "M5CGR"),
    }

    r = client.get("/api/clientes?q=999000222", headers=auth_headers)
    c = next((x for x in r.json() if x["nuit"] == "999000222"), None)
    if c:
        ctx["cliente_id"] = c["id"]
    else:
        r = client.post(
            "/api/clientes", headers=auth_headers,
            json={"nuit": "999000222", "nome": "Cliente M5c", "morada": "Rua B"},
        )
        ctx["cliente_id"] = r.json()["id"]

    r = client.get("/api/artigos?q=M5C-ART", headers=auth_headers)
    a = next((x for x in r.json() if x["codigo"] == "M5C-ART"), None)
    if a:
        ctx["artigo_id"] = a["id"]
    else:
        r = client.post(
            "/api/artigos", headers=auth_headers,
            json={
                "codigo": "M5C-ART",
                "descricao": "Artigo M5c",
                "unidade_id": 1,
                "imposto_id": 1,
                "preco_unitario": "116.00",
            },
        )
        ctx["artigo_id"] = r.json()["id"]

    return ctx


def _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=1):
    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": ctx["serie_ft"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": str(qty_por_linha),
            }],
        },
    )
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]
    r = client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------- FS ----------------


def test_criar_e_finalizar_fs(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "FS",
            "serie_id": ctx["serie_fs"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "linhas": [{"artigo_id": ctx["artigo_id"], "quantidade": "1"}],
        },
    )
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]
    r = client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["fiscal"] is True
    assert doc["hash"] is not None


# ---------------- NC ----------------


def test_nc_parcial(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    ft = _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=10)
    linha_ft_id = ft["linhas"][0]["id"]

    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "NC",
            "serie_id": ctx["serie_nc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "documento_origem_id": ft["id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": "3",
                "documento_origem_linha_id": linha_ft_id,
            }],
        },
    )
    assert r.status_code == 201, r.text
    nc_id = r.json()["id"]
    r = client.post(f"/api/documentos/{nc_id}/finalizar", headers=auth_headers)
    assert r.status_code == 200, r.text
    nc = r.json()
    assert nc["fiscal"] is True
    assert nc["hash"] is not None
    assert nc["documento_origem_id"] == ft["id"]
    assert Decimal(nc["total"]) == Decimal("348.0000")


def test_nc_sem_origem_falha(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "NC",
            "serie_id": ctx["serie_nc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "linhas": [{"artigo_id": ctx["artigo_id"], "quantidade": "1"}],
        },
    )
    assert r.status_code == 400
    assert "documento_origem_id" in r.json()["detail"].lower()


def test_nc_linha_origem_inexistente(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    ft = _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=5)
    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "NC",
            "serie_id": ctx["serie_nc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "documento_origem_id": ft["id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": "1",
                "documento_origem_linha_id": 999999,
            }],
        },
    )
    assert r.status_code == 400


def test_nc_linha_origem_doutro_doc(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    ft_a = _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=5)
    ft_b = _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=5)
    linha_ft_b = ft_b["linhas"][0]["id"]

    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "NC",
            "serie_id": ctx["serie_nc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "documento_origem_id": ft_a["id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": "1",
                "documento_origem_linha_id": linha_ft_b,
            }],
        },
    )
    assert r.status_code == 400
    assert "pertence" in r.json()["detail"].lower()


def test_nc_total_excede_origem(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    ft = _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=3)
    linha_ft_id = ft["linhas"][0]["id"]

    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "NC",
            "serie_id": ctx["serie_nc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "documento_origem_id": ft["id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": "4",
                "documento_origem_linha_id": linha_ft_id,
            }],
        },
    )
    nc_id = r.json()["id"]
    r = client.post(f"/api/documentos/{nc_id}/finalizar", headers=auth_headers)
    assert r.status_code == 400
    assert "excede" in r.json()["detail"].lower()


def test_nc_duas_excedem(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    ft = _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=10)
    linha_ft_id = ft["linhas"][0]["id"]

    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "NC",
            "serie_id": ctx["serie_nc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "documento_origem_id": ft["id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": "6",
                "documento_origem_linha_id": linha_ft_id,
            }],
        },
    )
    nc1_id = r.json()["id"]
    r = client.post(f"/api/documentos/{nc1_id}/finalizar", headers=auth_headers)
    assert r.status_code == 200

    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "NC",
            "serie_id": ctx["serie_nc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "documento_origem_id": ft["id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": "5",
                "documento_origem_linha_id": linha_ft_id,
            }],
        },
    )
    nc2_id = r.json()["id"]
    r = client.post(f"/api/documentos/{nc2_id}/finalizar", headers=auth_headers)
    assert r.status_code == 400
    assert "excede" in r.json()["detail"].lower()


# ---------------- ND ----------------


def test_nd_parcial(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    ft = _criar_ft_finalizada(client, auth_headers, ctx, qty_por_linha=5)
    linha_ft_id = ft["linhas"][0]["id"]

    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "ND",
            "serie_id": ctx["serie_nd"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "documento_origem_id": ft["id"],
            "linhas": [{
                "artigo_id": ctx["artigo_id"],
                "quantidade": "2",
                "documento_origem_linha_id": linha_ft_id,
            }],
        },
    )
    assert r.status_code == 201
    nd_id = r.json()["id"]
    r = client.post(f"/api/documentos/{nd_id}/finalizar", headers=auth_headers)
    assert r.status_code == 200
    assert Decimal(r.json()["total"]) == Decimal("232.0000")


# ---------------- Nao fiscais ----------------


def _criar_nao_fiscal(client, auth_headers, ctx, tipo, serie_id):
    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": tipo,
            "serie_id": serie_id,
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "linhas": [{"artigo_id": ctx["artigo_id"], "quantidade": "1"}],
        },
    )
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]
    r = client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_cotacao_nao_fiscal_sem_hash(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    doc = _criar_nao_fiscal(client, auth_headers, ctx, "COT", ctx["serie_cot"])
    assert doc["fiscal"] is False
    assert doc["hash"] is None
    assert doc["assinatura"] is None
    assert doc["estado"] == "finalizado"


def test_proforma_nao_fiscal_sem_hash(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    doc = _criar_nao_fiscal(client, auth_headers, ctx, "PRO", ctx["serie_pro"])
    assert doc["fiscal"] is False
    assert doc["hash"] is None


def test_guia_remessa_nao_fiscal_sem_hash(client, auth_headers):
    ctx = _criar_contexto(client, auth_headers)
    doc = _criar_nao_fiscal(client, auth_headers, ctx, "GR", ctx["serie_gr"])
    assert doc["fiscal"] is False
    assert doc["hash"] is None