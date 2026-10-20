from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.documento import Documento
from app.models.empresa import Empresa
from app.services.assinatura import verificar_documento

router = APIRouter(prefix="/api/public", tags=["public"])


def _codigo_valido(c: str) -> bool:
    return len(c) == 16 and all(ch in "0123456789abcdef" for ch in c.lower())


@router.get("/verificar/{codigo}")
def verificar(codigo: str, db: Session = Depends(get_db)):
    codigo = codigo.lower().strip()

    if not _codigo_valido(codigo):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Codigo de verificacao invalido (deve ter 16 caracteres hex).",
        )

    doc = (
        db.query(Documento)
        .filter(Documento.hash.like(f"{codigo}%"))
        .first()
    )

    if not doc:
        return {
            "valido": False,
            "motivo": "Documento nao encontrado",
            "codigo": codigo,
        }

    valido = verificar_documento(db, doc)
    empresa = db.query(Empresa).order_by(Empresa.id).first()

    return {
        "valido": valido,
        "motivo": None if valido else "Assinatura invalida ou adulterada",
        "codigo": codigo,
        "numero_formatado": doc.numero_formatado,
        "data": doc.data_documento.isoformat(),
        "total": str(doc.total),
        "cliente_nome": doc.cliente_nome,
        "estado": doc.estado.value,
        "emitente_nome": empresa.designacao if empresa else None,
        "emitente_nuit": empresa.nuit if empresa else None,
    }