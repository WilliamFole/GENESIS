from datetime import date

from sqlalchemy.orm import Session

from app.models.imposto import Imposto, TipoImposto
from app.models.metodo_pagamento import MetodoPagamento
from app.models.moeda import Moeda
from app.services import auditoria


def _seed_impostos(db: Session) -> None:
    hoje = date(2020, 1, 1)
    seeds = [
        {
            "codigo": "IVA16",
            "descricao": "IVA - taxa geral 16%",
            "tipo": TipoImposto.IVA,
            "percentagem": 16,
            "motivo_isencao": None,
        },
        {
            "codigo": "IVA0",
            "descricao": "IVA - taxa zero",
            "tipo": TipoImposto.IVA,
            "percentagem": 0,
            "motivo_isencao": None,
        },
        {
            "codigo": "ISE",
            "descricao": "Isento de IVA",
            "tipo": TipoImposto.ISENTO,
            "percentagem": 0,
            "motivo_isencao": "Isento por disposicao legal",
        },
    ]
    for s in seeds:
        if db.query(Imposto).filter(Imposto.codigo == s["codigo"]).first():
            continue
        imp = Imposto(**s, vigencia_inicio=hoje, ativo=True)
        db.add(imp)
        db.flush()
        auditoria.registar(
            db, operacao="seed_imposto", entidade="imposto",
            entidade_id=imp.id, detalhes=f"codigo={imp.codigo}",
        )
    db.commit()


def _seed_moeda_base(db: Session) -> None:
    if db.query(Moeda).filter(Moeda.codigo == "MZN").first():
        return
    mzn = Moeda(codigo="MZN", nome="Metical mocambicano", simbolo="MT", base=True, ativo=True)
    db.add(mzn)
    db.flush()
    auditoria.registar(
        db, operacao="seed_moeda_base", entidade="moeda",
        entidade_id=mzn.id, detalhes="MZN (moeda base)",
    )
    db.commit()


def _seed_metodos_pagamento(db: Session) -> None:
    seeds = [
        ("NUM", "Numerario"),
        ("TRF", "Transferencia"),
        ("CAR", "Cartao"),
        ("MPESA", "M-Pesa"),
        ("EMOLA", "e-Mola"),
        ("CHQ", "Cheque"),
    ]
    for codigo, nome in seeds:
        if db.query(MetodoPagamento).filter(MetodoPagamento.codigo == codigo).first():
            continue
        mp = MetodoPagamento(codigo=codigo, nome=nome, ativo=True)
        db.add(mp)
        db.flush()
        auditoria.registar(
            db, operacao="seed_metodo_pagamento", entidade="metodo_pagamento",
            entidade_id=mp.id, detalhes=f"codigo={codigo}",
        )
    db.commit()


def executar(db: Session) -> None:
    _seed_impostos(db)
    _seed_moeda_base(db)
    _seed_metodos_pagamento(db)