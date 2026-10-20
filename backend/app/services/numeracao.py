from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.documento import Documento, TipoDocumentoFiscal
from app.models.serie import Serie


def obter_serie_ativa(db: Session, serie_id: int, tipo: TipoDocumentoFiscal) -> Serie:
    serie = db.get(Serie, serie_id)
    if not serie:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Serie inexistente")
    if not serie.ativo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Serie fechada")
    if serie.tipo_documento.value != tipo.value:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Serie {serie.prefixo} nao e do tipo {tipo.value}",
        )
    return serie


def validar_data_nao_anterior(
    db: Session, serie_id: int, data_doc: date
) -> None:
    """
    RF-DOC-09: a data do documento nao pode ser anterior a do ultimo
    documento da mesma serie.
    """
    ultimo = (
        db.query(Documento)
        .filter(
            Documento.serie_id == serie_id,
            Documento.estado != "rascunho",
        )
        .order_by(Documento.data_documento.desc(), Documento.numero.desc())
        .first()
    )
    if ultimo and data_doc < ultimo.data_documento:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Data anterior ao ultimo documento da serie ({ultimo.data_documento})",
        )


def atribuir_numero(db: Session, serie: Serie) -> int:
    """
    Atribuicao atomica: UPDATE ... WHERE ultimo_numero = valor_atual.
    Em SQLite o UPDATE e serializado; a clausula WHERE com o valor atual
    evita saltos se dois pedidos chegarem ao mesmo tempo (o segundo falha
    e tentamos de novo).
    """
    for _ in range(5):
        atual = serie.ultimo_numero
        resultado = (
            db.query(Serie)
            .filter(Serie.id == serie.id, Serie.ultimo_numero == atual)
            .update({Serie.ultimo_numero: atual + 1}, synchronize_session=False)
        )
        if resultado == 1:
            db.flush()
            db.refresh(serie)
            return serie.ultimo_numero
        db.expire(serie)
    raise HTTPException(
        status.HTTP_409_CONFLICT,
        "Nao foi possivel atribuir numero (concorrencia). Tente novamente.",
    )


def formatar_numero(serie: Serie, numero: int) -> str:
    return f"{serie.tipo_documento.value} {serie.prefixo}/{numero}"