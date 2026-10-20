from datetime import date

from decimal import Decimal


def test_mapa_iva_vazio(client, auth_headers):
    # periodo sem documentos
    r = client.get("/api/fiscal/mapa-iva/2020/1", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["periodo"]["ano"] == 2020
    assert d["por_taxa"] == []
    assert d["totais"]["saldo_iva"] == "0.00"


def test_mapa_iva_com_documentos(client, auth_headers):
    # Cria serie + cliente + artigo se nao existirem
    r = client.get("/api/series", headers=auth_headers)
    e = next((s for s in r.json() if s["tipo_documento"] == "FT" and s["prefixo"] == "M9MFT"), None)
    if not e:
        r = client.post(
            "/api/series", headers=auth_headers,
            json={"tipo_documento": "FT", "prefixo": "M9MFT"},
        )
        serie_ft = r.json()["id"]
    else:
        serie_ft = e["id"]

    r = client.get("/api/clientes?q=999000444", headers=auth_headers)
    c = next((x for x in r.json() if x["nuit"] == "999000444"), None)
    if not c:
        r = client.post(
            "/api/clientes", headers=auth_headers,
            json={"nuit": "999000444", "nome": "Cliente M9Mapa", "morada": "Rua"},
        )
        cliente_id = r.json()["id"]
    else:
        cliente_id = c["id"]

    r = client.get("/api/artigos?q=M9M-ART", headers=auth_headers)
    a = next((x for x in r.json() if x["codigo"] == "M9M-ART"), None)
    if not a:
        r = client.post(
            "/api/artigos", headers=auth_headers,
            json={
                "codigo": "M9M-ART",
                "descricao": "Artigo M9Mapa",
                "unidade_id": 1,
                "imposto_id": 1,
                "preco_unitario": "116.00",
            },
        )
        artigo_id = r.json()["id"]
    else:
        artigo_id = a["id"]

    # Cria 2 FT finalizadas no periodo
    hoje = date.today()
    for _ in range(2):
        r = client.post(
            "/api/documentos", headers=auth_headers,
            json={
                "tipo_documento": "FT",
                "serie_id": serie_ft,
                "data_documento": hoje.isoformat(),
                "cliente_id": cliente_id,
                "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
            },
        )
        client.post(f"/api/documentos/{r.json()['id']}/finalizar", headers=auth_headers)

    r = client.get(f"/api/fiscal/mapa-iva/{hoje.year}/{hoje.month}", headers=auth_headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert len(d["por_taxa"]) >= 1
    # Procura a taxa 16%
    t16 = next((t for t in d["por_taxa"] if t["taxa"] == "16.00"), None)
    assert t16 is not None
    assert Decimal(t16["liquidado"]["iva"]) >= Decimal("32.00")
    assert Decimal(d["totais"]["saldo_iva"]) >= Decimal("32.00")


def test_gerar_saft(client, auth_headers):
    hoje = date.today()
    r = client.post(
        f"/api/fiscal/saft/{hoje.year}/{hoje.month}",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["tamanho_bytes"] > 100
    assert d["ficheiro_id"] > 0


def test_saft_download(client, auth_headers):
    hoje = date.today()
    r = client.post(
        f"/api/fiscal/saft/{hoje.year}/{hoje.month}",
        headers=auth_headers,
    )
    fid = r.json()["ficheiro_id"]
    r2 = client.get(f"/api/fiscal/ficheiros/{fid}/download", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.content.startswith(b"<?xml")
    assert b"AuditFile" in r2.content
    assert b"PROVISORIA" in r2.content


def test_mapa_iva_periodo_invalido(client, auth_headers):
    r = client.get("/api/fiscal/mapa-iva/2024/13", headers=auth_headers)
    assert r.status_code == 400


def test_saft_sem_token(client):
    r = client.post("/api/fiscal/saft/2024/1")
    assert r.status_code == 401