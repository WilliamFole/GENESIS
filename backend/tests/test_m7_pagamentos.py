from datetime import date, timedelta
from decimal import Decimal


def _ctx(client, auth_headers):
    """Cria serie FT, cliente, artigo, fatura finalizada."""
    r = client.get("/api/series", headers=auth_headers)
    e = next((s for s in r.json() if s["tipo_documento"] == "FT" and s["prefixo"] == "M7FT"), None)
    serie_ft = e["id"] if e else client.post(
        "/api/series", headers=auth_headers,
        json={"tipo_documento": "FT", "prefixo": "M7FT"},
    ).json()["id"]

    r = client.get("/api/clientes?q=999000777", headers=auth_headers)
    c = next((x for x in r.json() if x["nuit"] == "999000777"), None)
    cliente_id = c["id"] if c else client.post(
        "/api/clientes", headers=auth_headers,
        json={"nuit": "999000777", "nome": "Cliente M7", "morada": "Rua"},
    ).json()["id"]

    r = client.get("/api/artigos?q=M7-ART", headers=auth_headers)
    a = next((x for x in r.json() if x["codigo"] == "M7-ART"), None)
    artigo_id = a["id"] if a else client.post(
        "/api/artigos", headers=auth_headers,
        json={
            "codigo": "M7-ART", "descricao": "Artigo M7",
            "unidade_id": 1, "imposto_id": 1,
            "preco_unitario": "1160.00",
        },
    ).json()["id"]

    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "FT", "serie_id": serie_ft,
            "data_documento": date.today().isoformat(),
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "5"}],
        },
    )
    doc_id = r.json()["id"]
    client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)

    return {
        "serie_ft": serie_ft,
        "cliente_id": cliente_id,
        "artigo_id": artigo_id,
        "doc_id": doc_id,
    }


def test_saldo_por_pagar(client, auth_headers):
    ctx = _ctx(client, auth_headers)
    r = client.get(f"/api/pagamentos/saldo/{ctx['doc_id']}", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["estado_pagamento"] == "por_pagar"
    assert Decimal(d["valor_pago"]) == Decimal("0")


def test_criar_pagamento_parcial(client, auth_headers):
    ctx = _ctx(client, auth_headers)
    # Total = 5 * 1160 = 5800
    r = client.post(
        "/api/pagamentos", headers=auth_headers,
        json={
            "documento_id": ctx["doc_id"],
            "metodo_pagamento_id": 1,  # NUM
            "data_pagamento": date.today().isoformat(),
            "valor": "2000.00",
        },
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r2 = client.get(f"/api/pagamentos/saldo/{ctx['doc_id']}", headers=auth_headers)
    assert r2.json()["estado_pagamento"] == "parcial"
    assert Decimal(r2.json()["valor_pago"]) == Decimal("2000.00")


def test_criar_pagamento_pago(client, auth_headers):
    ctx = _ctx(client, auth_headers)
    r = client.post(
        "/api/pagamentos", headers=auth_headers,
        json={
            "documento_id": ctx["doc_id"],
            "metodo_pagamento_id": 1,
            "data_pagamento": date.today().isoformat(),
            "valor": "5800.00",
        },
    )
    assert r.status_code == 201
    r2 = client.get(f"/api/pagamentos/saldo/{ctx['doc_id']}", headers=auth_headers)
    assert r2.json()["estado_pagamento"] == "pago"
    assert Decimal(r2.json()["saldo"]) == Decimal("0")


def test_overpayment_falha(client, auth_headers):
    ctx = _ctx(client, auth_headers)
    r = client.post(
        "/api/pagamentos", headers=auth_headers,
        json={
            "documento_id": ctx["doc_id"],
            "metodo_pagamento_id": 1,
            "data_pagamento": date.today().isoformat(),
            "valor": "99999.00",
        },
    )
    assert r.status_code == 400


def test_referencia_obrigatoria_mpesa(client, auth_headers):
    ctx = _ctx(client, auth_headers)
    # metodo MPESA — descobrir id
    r = client.get("/api/metodos-pagamento", headers=auth_headers)
    mpesa = next(m for m in r.json() if m["codigo"] == "MPESA")

    r2 = client.post(
        "/api/pagamentos", headers=auth_headers,
        json={
            "documento_id": ctx["doc_id"],
            "metodo_pagamento_id": mpesa["id"],
            "data_pagamento": date.today().isoformat(),
            "valor": "100.00",
        },
    )
    assert r2.status_code == 400


def test_pagamento_documento_anulado_falha(client, auth_headers):
    ctx = _ctx(client, auth_headers)
    client.post(
        f"/api/documentos/{ctx['doc_id']}/anular",
        headers=auth_headers,
        json={"motivo_anulacao": "teste"},
    )
    r = client.post(
        "/api/pagamentos", headers=auth_headers,
        json={
            "documento_id": ctx["doc_id"],
            "metodo_pagamento_id": 1,
            "data_pagamento": date.today().isoformat(),
            "valor": "100.00",
        },
    )
    assert r.status_code == 400


def test_estorno_pagamento(client, auth_headers):
    ctx = _ctx(client, auth_headers)
    r = client.post(
        "/api/pagamentos", headers=auth_headers,
        json={
            "documento_id": ctx["doc_id"],
            "metodo_pagamento_id": 1,
            "data_pagamento": date.today().isoformat(),
            "valor": "1000.00",
        },
    )
    pid = r.json()["id"]

    r2 = client.post(
        f"/api/pagamentos/{pid}/estorno",
        headers=auth_headers,
        json={"motivo_estorno": "erro de registo"},
    )
    assert r2.status_code == 201
    assert Decimal(r2.json()["valor"]) == Decimal("-1000.00")

    # Tentar estornar duas vezes falha
    r3 = client.post(
        f"/api/pagamentos/{pid}/estorno",
        headers=auth_headers,
        json={"motivo_estorno": "outra"},
    )
    assert r3.status_code == 400