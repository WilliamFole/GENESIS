import sys
import json
import hashlib
from pathlib import Path
from typing import cast

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
except ImportError:
    print("Erro: A biblioteca 'cryptography' nao esta instalada.")
    input("Pressione ENTER para sair...")
    sys.exit(1)

COFRE_PATH = Path("cofre_licencas.pem")

def criar_cofre():
    print("\n--- CRIAR NOVO COFRE DE LICENÇAS (Apenas UMA VEZ) ---")
    passphrase = input("Defina a Passphrase Mestre (guarde-a bem!): ")
    if not passphrase:
        print("A passphrase nao pode ser vazia.")
        return

    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode())
    )
    
    COFRE_PATH.write_bytes(pem)
    print("\n✅ Cofre 'cofre_licencas.pem' criado com sucesso!")
    print("⚠️  IMPORTANTE: Copie este ficheiro para um PEN DRIVE seguro.")
    
    # Extrair chave pública para o sistema
    pub = priv.public_key()
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("\n--- COPIE O TEXTO ABAIXO PARA O FICHEIRO 'licenca.py' ---")
    print(pub_pem.decode('utf-8'))
    print("-----------------------------------------------------------\n")

def gerar_licenca():
    if not COFRE_PATH.exists():
        print("\n❌ Erro: Ficheiro 'cofre_licencas.pem' nao encontrado nesta pasta.")
        return

    print("\n--- GERAR NOVA LICENÇA ---")
    passphrase = input("Digite a Passphrase Mestre: ")
    
    try:
        priv = serialization.load_pem_private_key(
            COFRE_PATH.read_bytes(),
            password=passphrase.encode(),
        )
    except ValueError:
        print("\n❌ Passphrase incorreta!")
        return

    priv = cast(rsa.RSAPrivateKey, priv)

    cliente = input("Nome da Empresa: ")
    nuit = input("NUIT: ")
    validade = input("Validade (AAAA-MM-DD): ")

    payload = json.dumps(
        {"cliente": cliente, "nuit": nuit, "validade": validade}
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
    
    print(f"\n✅ Licença gerada: {nome_ficheiro}")
    print("O ficheiro esta pronto a ser enviado para o cliente.")

def main():
    while True:
        print("\n===================================")
        print("      GERADOR DE LICENÇAS SGE      ")
        print("===================================")
        print("1. Criar Cofre (Fazer apenas 1 vez)")
        print("2. Gerar Licença (Cliente)")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opcao (1/2/3): ")
        
        if opcao == '1':
            criar_cofre()
        elif opcao == '2':
            gerar_licenca()
        elif opcao == '3':
            break
        else:
            print("Opcao invalida.")

if __name__ == "__main__":
    main()