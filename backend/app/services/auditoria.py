from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria
from app.models.utilizador import Utilizador


def registar(
    db: Session,
    *,
    operacao: str,
    utilizador: Utilizador | None = None,
    entidade: str | None = None,
    entidade_id: int | str | None = None,
    detalhes: str | None = None,
    ip: str | None = None,
) -> Auditoria:
    reg = Auditoria(
        utilizador_id=utilizador.id if utilizador else None,
        username=utilizador.username if utilizador else None,
        operacao=operacao,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id is not None else None,
        detalhes=detalhes,
        ip=ip,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return reg