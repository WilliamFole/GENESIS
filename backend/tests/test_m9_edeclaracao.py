from datetime import date

import pytest


def _obter_ou_criar_serie(client, auth_headers, tipo, prefixo):
    r = client.get("/api/series", headers=auth_headers)
    e = next((s for s in r.json() if s["tipo_documento"] == tipo and s["prefixo"] == prefixo), None)
    if e:
        return e["id"]
    r = client.post(
        "/api/series", headers=auth_headers,
        json={"tipo_documento": tipo, "prefixo": prefixo},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _preparar_documentos(client, auth_headers):
    serie_ft = _obter_ou_criar_serie(client, auth_headers, "FT", "M9FT")

    r = client.get("/api/clientes?q=999000333", headers=auth_headers)
    c = next((x for x in r.json() if x["nuit"] == "999000333"), None)
    if c:
        cliente_id = c["id"]
    else:
        r = client.post(
            "/api/clientes", headers=auth_headers,
            json={"nuit": "999000333", "nome": "Cliente M9", "morada": "Rua M9"},
        )
        cliente_id = r.json()["id"]

    r = client.get("/api/artigos?q=M9-ART", headers=auth_headers)
    a = next((x for x in r.json() if x["codigo"] == "M9-ART"), None)
    if a:
        artigo_id = a["id"]
    else:
        r = client.post(
            "/api/artigos", headers=auth_headers,
            json={
                "codigo": "M9-ART",
                "descricao": "Artigo M9",
                "unidade_id": 1,
                "imposto_id": 1,
                "preco_unitario": "116.00",
            },
        )
        artigo_id = r.json()["id"]

    # Cria 2 faturas finalizadas
    for _ in range(2):
        r = client.post(
            "/api/documentos", headers=auth_headers,
            json={
                "tipo_documento": "FT",
                "serie_id": serie_ft,
                "data_documento": date.today().isoformat(),
                "cliente_id": cliente_id,
                "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
            },
        )
        assert r.status_code == 201, r.text
        client.post(f"/api/documentos/{r.json()['id']}/finalizar", headers=auth_headers)


def test_gerar_edeclaracao_xml(client, auth_headers):
    _preparar_documentos(client, auth_headers)
    hoje = date.today()
    r = client.post(
        f"/api/fiscal/edeclaracao/{hoje.year}/{hoje.month}?formato=xml",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    dados = r.json()
    assert dados["formato"] == "xml"
    assert len(dados["partes"]) >= 1
    assert dados["numero_documentos"] >= 2


def test_gerar_edeclaracao_xlsx(client, auth_headers):
    _preparar_documentos(client, auth_headers)
    hoje = date.today()
    r = client.post(
        f"/api/fiscal/edeclaracao/{hoje.year}/{hoje.month}?formato=xlsx",
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    dados = r.json()
    assert dados["formato"] == "xlsx"
    assert len(dados["partes"]) >= 1


def test_download_ficheiro(client, auth_headers):
    hoje = date.today()
    r = client.post(
        f"/api/fiscal/edeclaracao/{hoje.year}/{hoje.month}?formato=xml",
        headers=auth_headers,
    )
    parte_id = r.json()["partes"][0]["id"]
    r2 = client.get(f"/api/fiscal/ficheiros/{parte_id}/download", headers=auth_headers)
    assert r2.status_code == 200
    assert len(r2.content) > 0


def test_listar_ficheiros(client, auth_headers):
    r = client.get("/api/fiscal/ficheiros", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_periodo_invalido(client, auth_headers):
    r = client.post("/api/fiscal/edeclaracao/2024/13?formato=xml", headers=auth_headers)
    assert r.status_code == 400


def test_formato_invalido(client, auth_headers):
    hoje = date.today()
    r = client.post(
        f"/api/fiscal/edeclaracao/{hoje.year}/{hoje.month}?formato=pdf",
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_sem_token(client):
    hoje = date.today()
    r = client.post(f"/api/fiscal/edeclaracao/{hoje.year}/{hoje.month}?formato=xml")
    assert r.status_code == 401