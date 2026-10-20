from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.documento import (
    Documento,
    EstadoDocumento,
    LinhaDocumento,
    TipoDocumentoFiscal,
)

# Documentos que liquidam IVA (aumentam o IVA a pagar)
_TIPOS_LIQUIDACAO = {
    TipoDocumentoFiscal.FT,
    TipoDocumentoFiscal.VD,
    TipoDocumentoFiscal.FS,
    TipoDocumentoFiscal.ND,
}

# Documentos que deduzem IVA (reduzem o IVA a pagar)
_TIPOS_DEDUCAO = {TipoDocumentoFiscal.NC}


def _periodo(ano: int, mes: int) -> tuple[date, date]:
    inicio = date(ano, mes, 1)
    fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, fim


def calcular_mapa_iva(db: Session, ano: int, mes: int) -> dict:
    """
    Devolve:
      {
        "periodo": {"ano", "mes"},
        "por_taxa": [
          {"taxa": Decimal, "liquidado": {...}, "dedutivel": {...}, "saldo": {...}},
          ...
        ],
        "totais": {"liquidado_base", "liquidado_iva", "dedutivel_base",
                   "dedutivel_iva", "saldo_base", "saldo_iva"},
        "documentos": {"liquidacao": int, "deducao": int, "anulados": int},
      }
    """
    inicio, fim = _periodo(ano, mes)

    docs = (
        db.query(Documento)
        .filter(
            Documento.fiscal.is_(True),
            Documento.estado == EstadoDocumento.FINALIZADO,
            Documento.data_documento >= inicio,
            Documento.data_documento < fim,
        )
        .all()
    )

    anulados = (
        db.query(Documento)
        .filter(
            Documento.fiscal.is_(True),
            Documento.estado == EstadoDocumento.ANULADO,
            Documento.data_documento >= inicio,
            Documento.data_documento < fim,
        )
        .count()
    )

    # Agrega por taxa
    # {taxa: {"liquidado": {"base": Decimal, "iva": Decimal}, "dedutivel": {...}}}
    por_taxa: dict[Decimal, dict] = {}

    def _get_bucket(taxa: Decimal) -> dict:
        if taxa not in por_taxa:
            por_taxa[taxa] = {
                "liquidado": {"base": Decimal("0"), "iva": Decimal("0")},
                "dedutivel": {"base": Decimal("0"), "iva": Decimal("0")},
            }
        return por_taxa[taxa]

    n_liquidacao = 0
    n_deducao = 0

    for d in docs:
        if d.tipo_documento in _TIPOS_LIQUIDACAO:
            alvo = "liquidado"
            n_liquidacao += 1
        elif d.tipo_documento in _TIPOS_DEDUCAO:
            alvo = "dedutivel"
            n_deducao += 1
        else:
            continue

        # Soma pelas linhas (taxa real de cada linha)
        for linha in d.linhas:
            bucket = _get_bucket(linha.taxa_iva)
            bucket[alvo]["base"] += linha.base_tributavel
            bucket[alvo]["iva"] += linha.valor_iva

    # Monta resposta
    por_taxa_lista: list[dict] = []
    tot_liq_base = tot_liq_iva = Decimal("0")
    tot_ded_base = tot_ded_iva = Decimal("0")

    for taxa in sorted(por_taxa.keys(), reverse=True):
        b = por_taxa[taxa]
        liq_base = b["liquidado"]["base"]
        liq_iva = b["liquidado"]["iva"]
        ded_base = b["dedutivel"]["base"]
        ded_iva = b["dedutivel"]["iva"]
        saldo_base = liq_base - ded_base
        saldo_iva = liq_iva - ded_iva

        por_taxa_lista.append({
            "taxa": f"{taxa:.2f}",
            "liquidado": {"base": f"{liq_base:.2f}", "iva": f"{liq_iva:.2f}"},
            "dedutivel": {"base": f"{ded_base:.2f}", "iva": f"{ded_iva:.2f}"},
            "saldo": {"base": f"{saldo_base:.2f}", "iva": f"{saldo_iva:.2f}"},
        })

        tot_liq_base += liq_base
        tot_liq_iva += liq_iva
        tot_ded_base += ded_base
        tot_ded_iva += ded_iva

    return {
        "periodo": {"ano": ano, "mes": mes},
        "por_taxa": por_taxa_lista,
        "totais": {
            "liquidado_base": f"{tot_liq_base:.2f}",
            "liquidado_iva": f"{tot_liq_iva:.2f}",
            "dedutivel_base": f"{tot_ded_base:.2f}",
            "dedutivel_iva": f"{tot_ded_iva:.2f}",
            "saldo_base": f"{tot_liq_base - tot_ded_base:.2f}",
            "saldo_iva": f"{tot_liq_iva - tot_ded_iva:.2f}",
        },
        "documentos": {
            "liquidacao": n_liquidacao,
            "deducao": n_deducao,
            "anulados": anulados,
        },
    }