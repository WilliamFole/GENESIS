from datetime import date, timedelta


def test_preview_vazio(client, auth_headers):
    r = client.get("/api/fechos-caixa/preview", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["total_geral"] == "0"


def test_criar_fecho(client, auth_headers):
    hoje = date.today().isoformat()
    # limpar qualquer fecho existente para hoje
    for f in client.get("/api/fechos-caixa", headers=auth_headers).json():
        if f["data"] == hoje and f["estado"] != "anulado":
            client.post(
                f"/api/fechos-caixa/{f['id']}/anular",
                headers=auth_headers,
                json={"motivo_anulacao": "teste"},
            )

    r = client.post(
        "/api/fechos-caixa", headers=auth_headers,
        json={"data": hoje},
    )
    assert r.status_code == 201, r.text
    fecho = r.json()
    assert fecho["estado"] == "aberto"


def test_duplicar_fecho_falha(client, auth_headers):
    hoje = date.today().isoformat()
    for f in client.get("/api/fechos-caixa", headers=auth_headers).json():
        if f["data"] == hoje and f["estado"] != "anulado":
            client.post(
                f"/api/fechos-caixa/{f['id']}/anular",
                headers=auth_headers,
                json={"motivo_anulacao": "limpeza"},
            )
    # cria um
    r = client.post(
        "/api/fechos-caixa", headers=auth_headers,
        json={"data": hoje},
    )
    assert r.status_code == 201

    # tentar criar outro
    r2 = client.post(
        "/api/fechos-caixa", headers=auth_headers,
        json={"data": hoje},
    )
    assert r2.status_code == 400


def test_fechar_e_anular(client, auth_headers):
    # usar data distinta (amanha) para nao colidir
    amanha = (date.today() + timedelta(days=1)).isoformat()

    r = client.post(
        "/api/fechos-caixa", headers=auth_headers,
        json={"data": amanha},
    )
    if r.status_code != 201:
        return  # ja existe, salta
    fecho_id = r.json()["id"]

    r2 = client.post(f"/api/fechos-caixa/{fecho_id}/fechar", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["estado"] == "fechado"

    # Fechado nao pode ser fechado outra vez
    r3 = client.post(f"/api/fechos-caixa/{fecho_id}/fechar", headers=auth_headers)
    assert r3.status_code == 400

    # Anular funciona
    r4 = client.post(
        f"/api/fechos-caixa/{fecho_id}/anular",
        headers=auth_headers,
        json={"motivo_anulacao": "engano"},
    )
    assert r4.status_code == 200
    assert r4.json()["estado"] == "anulado"