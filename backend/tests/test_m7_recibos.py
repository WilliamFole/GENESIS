from datetime import date
from decimal import Decimal


def _setup_fatura(client, auth_headers):
    r = client.get("/api/series", headers=auth_headers)
    e = next((s for s in r.json() if s["tipo_documento"] == "FT" and s["prefixo"] == "M7RF"), None)
    serie_ft = e["id"] if e else client.post(
        "/api/series", headers=auth_headers,
        json={"tipo_documento": "FT", "prefixo": "M7RF"},
    ).json()["id"]

    e = next((s for s in client.get("/api/series", headers=auth_headers).json()
              if s["tipo_documento"] == "RC" and s["prefixo"] == "M7RC"), None)
    serie_rc = e["id"] if e else client.post(
        "/api/series", headers=auth_headers,
        json={"tipo_documento": "RC", "prefixo": "M7RC"},
    ).json()["id"]

    r = client.get("/api/clientes?q=999000888", headers=auth_headers)
    c = next((x for x in r.json() if x["nuit"] == "999000888"), None)
    cliente_id = c["id"] if c else client.post(
        "/api/clientes", headers=auth_headers,
        json={"nuit": "999000888", "nome": "Cliente M7R", "morada": "Rua"},
    ).json()["id"]

    r = client.get("/api/artigos?q=M7R-ART", headers=auth_headers)
    a = next((x for x in r.json() if x["codigo"] == "M7R-ART"), None)
    artigo_id = a["id"] if a else client.post(
        "/api/artigos", headers=auth_headers,
        json={
            "codigo": "M7R-ART", "descricao": "Artigo M7R",
            "unidade_id": 1, "imposto_id": 1, "preco_unitario": "116.00",
        },
    ).json()["id"]

    # Cria 2 faturas finalizadas
    ids = []
    for _ in range(2):
        r = client.post(
            "/api/documentos", headers=auth_headers,
            json={
                "tipo_documento": "FT", "serie_id": serie_ft,
                "data_documento": date.today().isoformat(),
                "cliente_id": cliente_id,
                "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
            },
        )
        doc_id = r.json()["id"]
        client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)
        ids.append(doc_id)

    return {
        "serie_rc": serie_rc,
        "cliente_id": cliente_id,
        "faturas": ids,
    }


def _pagar(client, auth_headers, doc_id, valor):
    r = client.post(
        "/api/pagamentos", headers=auth_headers,
        json={
            "documento_id": doc_id,
            "metodo_pagamento_id": 1,
            "data_pagamento": date.today().isoformat(),
            "valor": valor,
        },
    )
    return r.json()["id"]


def test_criar_recibo_multi_fatura(client, auth_headers):
    ctx = _setup_fatura(client, auth_headers)
    p1 = _pagar(client, auth_headers, ctx["faturas"][0], "116.00")
    p2 = _pagar(client, auth_headers, ctx["faturas"][1], "116.00")

    r = client.post(
        "/api/recibos", headers=auth_headers,
        json={
            "serie_id": ctx["serie_rc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "pagamentos_ids": [p1, p2],
        },
    )
    assert r.status_code == 201, r.text
    rc = r.json()
    assert rc["tipo_documento"] == "RC"
    assert rc["estado"] == "rascunho"
    assert Decimal(rc["total"]) == Decimal("232.00")
    assert len(rc["linhas"]) == 2


def test_recibo_pagamento_repetido_falha(client, auth_headers):
    ctx = _setup_fatura(client, auth_headers)
    p1 = _pagar(client, auth_headers, ctx["faturas"][0], "116.00")

    r = client.post(
        "/api/recibos", headers=auth_headers,
        json={
            "serie_id": ctx["serie_rc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "pagamentos_ids": [p1],
        },
    )
    assert r.status_code == 201

    r2 = client.post(
        "/api/recibos", headers=auth_headers,
        json={
            "serie_id": ctx["serie_rc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "pagamentos_ids": [p1],
        },
    )
    assert r2.status_code == 400


def test_finalizar_recibo(client, auth_headers):
    ctx = _setup_fatura(client, auth_headers)
    p1 = _pagar(client, auth_headers, ctx["faturas"][0], "116.00")

    r = client.post(
        "/api/recibos", headers=auth_headers,
        json={
            "serie_id": ctx["serie_rc"],
            "data_documento": date.today().isoformat(),
            "cliente_id": ctx["cliente_id"],
            "pagamentos_ids": [p1],
        },
    )
    rc_id = r.json()["id"]
    r2 = client.post(f"/api/documentos/{rc_id}/finalizar", headers=auth_headers)
    assert r2.status_code == 200, r2.text
    assert r2.json()["estado"] == "finalizado"
    assert r2.json()["hash"] is not None