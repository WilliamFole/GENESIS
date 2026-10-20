import json
from pathlib import Path
from typing import cast

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def gerar_chaves():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()

    Path("private_key.pem").write_bytes(
        priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    Path("public_key.pem").write_bytes(
        pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def criar_licenca(cliente: str, nuit: str, validade_str: str):
    priv = cast(
        rsa.RSAPrivateKey,
        serialization.load_pem_private_key(
            Path("private_key.pem").read_bytes(), password=None
        ),
    )

    payload = json.dumps(
        {"cliente": cliente, "nuit": nuit, "validade": validade_str}
    ).encode("utf-8")

    assinatura = priv.sign(
        payload,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    conteudo = f"{assinatura.hex()}\n".encode("utf-8") + payload
    nome_ficheiro = f"licenca_{cliente.replace(' ', '_').lower()}.lic"
    Path(nome_ficheiro).write_bytes(conteudo)
    print(f"\n✅ Licença gerada com sucesso: {nome_ficheiro}")


if __name__ == "__main__":
    print("--- GERADOR DE LICENÇAS GENESIS ---")
    
    # 1. Gerar chaves se não existirem
    if not Path("private_key.pem").exists():
        print("A gerar chaves criptográficas pela primeira vez...")
        gerar_chaves()
        print("\n⚠️  IMPORTANTE:")
        print("1. Abre o ficheiro 'public_key.pem' e copia todo o seu conteúdo.")
        print("2. Cola no ficheiro 'app/services/licenca.py' na variável PUBLIC_KEY_PEM.")
        print("3. GUARDA o 'private_key.pem' num local seguro (nunca o apagues!).")
        input("\nPressiona ENTER depois de copiares a chave pública para o código...\n")

    # 2. Pedir dados da licença
    cliente = input("Nome do Cliente (ex: X, Lda): ")
    nuit = input("NUIT do Cliente (ex: 999999999): ")
    validade = input("Data de Validade (Formato AAAA-MM-DD, ex: 2027-12-31): ")
    
    criar_licenca(cliente, nuit, validade)