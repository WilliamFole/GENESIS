import base64
import hashlib
import json
from datetime import datetime

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import utcnow
from app.models.chave_assinatura import ChaveAssinatura


# ---------- Fernet para cifrar chave privada ----------


def _fernet() -> Fernet:
    """
    Deriva uma chave Fernet a partir de SECRET_KEY, de forma estavel
    (mesma SECRET_KEY -> mesma chave Fernet).
    """
    raw = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def _cifrar(pem_bytes: bytes) -> str:
    return _fernet().encrypt(pem_bytes).decode("ascii")


def _decifrar(token: str) -> bytes:
    return _fernet().decrypt(token.encode("ascii"))


# ---------- Ciclo de vida das chaves ----------


def obter_ativa(db: Session) -> ChaveAssinatura | None:
    return (
        db.query(ChaveAssinatura)
        .filter(ChaveAssinatura.ativa.is_(True))
        .order_by(ChaveAssinatura.id.desc())
        .first()
    )


def criar_ou_obter_ativa(db: Session) -> ChaveAssinatura:
    """
    Devolve a chave ativa. Se nao existir, gera uma nova.
    """
    atual = obter_ativa(db)
    if atual:
        return atual

    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem_priv = chave.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pem_pub = chave.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    reg = ChaveAssinatura(
        chave_privada_cifrada=_cifrar(pem_priv),
        chave_publica_pem=pem_pub.decode("ascii"),
        ativa=True,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg


def revogar_ativa(db: Session, motivo: str) -> ChaveAssinatura | None:
    atual = obter_ativa(db)
    if not atual:
        return None
    atual.ativa = False
    atual.motivo_revogacao = motivo
    atual.revogada_em = utcnow()
    db.commit()
    db.refresh(atual)
    return atual


# ---------- Assinatura ----------


def assinar(payload_bytes: bytes, chave: ChaveAssinatura) -> str:
    pem = _decifrar(chave.chave_privada_cifrada)
    private_key = serialization.load_pem_private_key(pem, password=None)
    assinatura = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(assinatura).decode("ascii")


def verificar(payload_bytes: bytes, assinatura_b64: str, chave: ChaveAssinatura) -> bool:
    try:
        pub = serialization.load_pem_public_key(chave.chave_publica_pem.encode("ascii"))
        assinatura = base64.b64decode(assinatura_b64.encode("ascii"))
        pub.verify(
            assinatura,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False


# ---------- Hash encadeado ----------


def _normalizar_datetime(v) -> str:
    if isinstance(v, datetime):
        return v.isoformat()
    if v is None:
        return ""
    return str(v)


def calcular_hash(
    *,
    tipo: str,
    serie_prefixo: str,
    numero: int,
    data_documento: str,
    cliente_nuit: str,
    total: str,
    hash_anterior: str | None,
) -> str:
    """
    Devolve hex do SHA-256 de uma string canonica.
    O hash_anterior (hex) do ultimo finalizado da mesma serie encadeia.
    """
    payload = {
        "tipo": tipo,
        "serie": serie_prefixo,
        "numero": numero,
        "data": data_documento,
        "cliente_nuit": cliente_nuit,
        "total": total,
        "hash_anterior": hash_anterior or "",
    }
    texto = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def payload_assinado(hash_hex: str) -> bytes:
    return hash_hex.encode("utf-8")


def codigo_publico(hash_hex: str) -> str:
    return hash_hex[:16]


def verificar_documento(db, doc) -> bool:
    """
    Verifica a assinatura do documento tentando todas as chaves conhecidas
    (ativas ou revogadas). Se uma delas validar, consideramos autentico.
    """
    if not doc.hash or not doc.assinatura:
        return False
    payload = payload_assinado(doc.hash)
    for chave in db.query(ChaveAssinatura).all():
        if verificar(payload, doc.assinatura, chave):
            return True
    return False