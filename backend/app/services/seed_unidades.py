from sqlalchemy.orm import Session

from app.models.unidade import Unidade
from app.services import auditoria


SEEDS = [
    ("UN", "Unidade"),
    ("KG", "Quilograma"),
    ("L", "Litro"),
    ("M", "Metro"),
    ("M2", "Metro quadrado"),
    ("H", "Hora"),
    ("CX", "Caixa"),
    ("PAR", "Par"),
    ("SRV", "Servico"),
]


def executar(db: Session) -> None:
    criados = 0
    for codigo, nome in SEEDS:
        if db.query(Unidade).filter(Unidade.codigo == codigo).first():
            continue
        u = Unidade(codigo=codigo, nome=nome, ativo=True)
        db.add(u)
        db.flush()
        auditoria.registar(
            db, operacao="seed_unidade", entidade="unidade",
            entidade_id=u.id, detalhes=f"codigo={codigo}",
        )
        criados += 1
    if criados:
        db.commit()