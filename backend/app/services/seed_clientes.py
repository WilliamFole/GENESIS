from sqlalchemy.orm import Session

from app.models.cliente import Cliente


def executar(db: Session) -> None:
    """
    Garante que o cliente 'Consumidor final' existe.
    Idempotente: pode correr em cada arranque sem duplicar.
    """
    existente = db.query(Cliente).filter(Cliente.nuit == "999999999").first()
    if existente:
        # Se existir mas com o flag a 0, repõe
        if not existente.consumidor_final:
            existente.consumidor_final = True
            db.commit()
        return

    cliente = Cliente(
        nuit="999999999",
        nome="Consumidor final",
        morada="Nao aplicavel",
        ativo=True,
        consumidor_final=True,
    )
    db.add(cliente)
    db.commit()