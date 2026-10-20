import json
from datetime import date, datetime
from typing import cast

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.core.paths import DATA_DIR

LICENCA_PATH = DATA_DIR / "licenca.lic"
PUBLIC_KEY_PATH = DATA_DIR / "public_key.pem"

PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4qNSsSJqJGl4EndmhCiM
q8Gd0I/xOkaVXR7AB3mQZDzHkRPO9ENSpcrmd4ZzGJ8ZzhNgGNghWnuR3+GubH+t
3wUsS1QX8EmwpPrrMW+n7rbdFQoGmIRwxQvM8OctoCIMuUTMXpGvlPP6vnjBZnLH
SYaK05hXN7di7MztaL/JNdgnBfhz0ZRYQUusz8L3/T5WCUL/UQ2x9ZnJjWyBlfCb
6RmtyvNW2z9332MrtFSXX+hFEhgrdYm6yvTkodh745QPShS8iLcCpGUQFonVJT5y
+bTrlu4EV/QKwIwL39BtJm5TLjOlPZSNGwSlqXrMyWa7mRuIsIYyyD8nz1089RWx
mwIDAQAB
-----END PUBLIC KEY-----"""



def _obter_chave_publica() -> rsa.RSAPublicKey:
    if PUBLIC_KEY_PATH.exists():
        key = serialization.load_pem_public_key(PUBLIC_KEY_PATH.read_bytes())
    else:
        key = serialization.load_pem_public_key(PUBLIC_KEY_PEM)
        
    return cast(rsa.RSAPublicKey, key)


def obter_status_licenca() -> dict:
    if not LICENCA_PATH.exists():
        return {"status": "ausente", "cliente": "Modo de Demonstração", "validade": None}

    try:
        conteudo = LICENCA_PATH.read_bytes()
        chave_publica = _obter_chave_publica()

        partes = conteudo.split(b"\n", 1)
        if len(partes) != 2:
            return {"status": "invalida", "cliente": "Licença Corrompida", "validade": None}

        assinatura, payload = partes

        chave_publica.verify(
            bytes.fromhex(assinatura.decode("utf-8")),
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        dados = json.loads(payload.decode("utf-8"))
        validade = datetime.strptime(dados["validade"], "%Y-%m-%d").date()
        hoje = date.today()

        if validade < hoje:
            return {
                "status": "expirada",
                "cliente": dados["cliente"],
                "nuit": dados.get("nuit"),
                "validade": validade.isoformat(),
            }

        return {
            "status": "ativa",
            "cliente": dados["cliente"],
            "nuit": dados.get("nuit"),
            "validade": validade.isoformat(),
        }

    except Exception:
        return {"status": "invalida", "cliente": "Erro na Licença", "validade": None}