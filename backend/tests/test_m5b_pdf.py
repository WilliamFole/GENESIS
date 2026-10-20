from datetime import date
from decimal import Decimal


def _criar_doc_finalizado(client, auth_headers):
    """Cria serie + cliente + artigo + documento e finaliza."""
    # Serie (idempotente)
    r = client.get("/api/series", headers=auth_headers)
    existente = next(
        (s for s in r.json() if s["tipo_documento"] == "FT" and s["prefixo"] == "PDFT"),
        None,
    )
    if existente:
        serie_id = existente["id"]
    else:
        r = client.post(
            "/api/series", headers=auth_headers,
            json={"tipo_documento": "FT", "prefixo": "PDFT"},
        )
        serie_id = r.json()["id"]

    # Cliente
    r = client.get("/api/clientes?q=999000111", headers=auth_headers)
    c = next((x for x in r.json() if x["nuit"] == "999000111"), None)
    if c:
        cliente_id = c["id"]
    else:
        r = client.post(
            "/api/clientes", headers=auth_headers,
            json={"nuit": "999000111", "nome": "Cliente PDF", "morada": "Rua X"},
        )
        cliente_id = r.json()["id"]

    # Artigo
    r = client.get("/api/artigos?q=SRV-M5A", headers=auth_headers)
    a = next((x for x in r.json() if x["codigo"] == "SRV-M5A"), None)
    if a:
        artigo_id = a["id"]
    else:
        r = client.post(
            "/api/artigos", headers=auth_headers,
            json={
                "codigo": "SRV-M5A",
                "descricao": "Servico",
                "unidade_id": 9,
                "imposto_id": 1,
                "preco_unitario": "116.00",
            },
        )
        artigo_id = r.json()["id"]

    # Documento + finalizar
    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": serie_id,
            "data_documento": date.today().isoformat(),
            "cliente_id": cliente_id,
            "linhas": [{"artigo_id": artigo_id, "quantidade": "1"}],
        },
    )
    doc_id = r.json()["id"]
    r = client.post(f"/api/documentos/{doc_id}/finalizar", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_gerar_pdf(client, auth_headers):
    import io
    from pypdf import PdfReader

    doc = _criar_doc_finalizado(client, auth_headers)
    r = client.get(f"/api/documentos/{doc['id']}/pdf", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")

    reader = PdfReader(io.BytesIO(r.content))
    assert len(reader.pages) == 2

    texto_1 = reader.pages[0].extract_text()
    texto_2 = reader.pages[1].extract_text()

    assert "ORIGINAL" in texto_1
    assert "DUPLICADO" in texto_2
    assert doc["numero_formatado"] in texto_1
    assert doc["cliente_nome"] in texto_1


def test_pdf_rascunho_bloqueado(client, auth_headers):
    doc = _criar_doc_finalizado(client, auth_headers)
    # cria outro rascunho
    r = client.post(
        "/api/documentos", headers=auth_headers,
        json={
            "tipo_documento": "FT",
            "serie_id": doc["serie_id"],
            "data_documento": date.today().isoformat(),
            "cliente_id": doc["cliente_id"],
            "linhas": [{"artigo_id": 1, "quantidade": "1"}],
        },
    )
    r2 = client.get(f"/api/documentos/{r.json()['id']}/pdf", headers=auth_headers)
    assert r2.status_code == 400


def test_pdf_sem_token(client):
    r = client.get("/api/documentos/1/pdf")
    assert r.status_code == 401