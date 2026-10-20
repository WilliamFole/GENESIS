from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.config import settings
from app.core.database import get_db
from app.core.security import utcnow
from app.models.artigo import Artigo
from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.documento import (
    Documento,
    EstadoDocumento,
    LinhaDocumento,
    TipoDocumentoFiscal,
)
from app.models.imposto import Imposto
from app.models.moeda import Moeda
from app.models.serie import Serie
from app.models.unidade import Unidade
from app.models.utilizador import Perfil, Utilizador
from app.schemas.documento import (
    DocumentoAnular,
    DocumentoCreate,
    DocumentoRead,
    DocumentoUpdate,
    LinhaCreate,
)
from app.services import auditoria
from app.services import assinatura, pdf
from app.services.numeracao import (
    atribuir_numero,
    formatar_numero,
    obter_serie_ativa,
    validar_data_nao_anterior,
)

router = APIRouter(prefix="/api/documentos", tags=["documentos"])

_pode_faturar = require_perfis(Perfil.ADMINISTRADOR, Perfil.FATURACAO)


# ---------------------------------------------------------------- helpers


def _round_2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _round_4(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _obter_ou_404(db: Session, doc_id: int) -> Documento:
    d = db.get(Documento, doc_id)
    if not d:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento nao encontrado")
    return d


def _garantir_rascunho(d: Documento) -> None:
    if d.estado != EstadoDocumento.RASCUNHO:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Documento em estado '{d.estado.value}' nao pode ser alterado",
        )


# Tipos que geram obrigacao fiscal. Documentos nao fiscais (COT/PRO/GR)
# nao entram na cadeia de hash nem no SAF-T.
_TIPOS_NAO_FISCAIS = {
    TipoDocumentoFiscal.COT,
    TipoDocumentoFiscal.PRO,
    TipoDocumentoFiscal.GR,
}

# Tipos que exigem um documento de origem (FT/VD/FS) finalizado.
_TIPOS_COM_ORIGEM = {
    TipoDocumentoFiscal.NC,
    TipoDocumentoFiscal.ND,
    TipoDocumentoFiscal.RC,
}


def _e_fiscal(tipo: TipoDocumentoFiscal) -> bool:
    return tipo not in _TIPOS_NAO_FISCAIS


def _validar_documento_origem(
    db: Session, tipo: TipoDocumentoFiscal, origem_id: int | None
) -> Documento | None:
    if tipo not in _TIPOS_COM_ORIGEM:
        return None
    if not origem_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"{tipo.value} exige documento_origem_id",
        )
    origem = db.get(Documento, origem_id)
    if not origem:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Documento de origem nao encontrado")
    if origem.estado != EstadoDocumento.FINALIZADO:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Documento de origem tem de estar finalizado",
        )
    if origem.tipo_documento not in (
        TipoDocumentoFiscal.FT,
        TipoDocumentoFiscal.VD,
        TipoDocumentoFiscal.FS,
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Apenas FT, VD ou FS podem ser origem de NC/ND/RC",
        )
    return origem


def _validar_linha_origem(
    db: Session, origem: Documento | None, origem_linha_id: int | None
):
    if origem_linha_id is None:
        return
    if origem is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Linha refere origem mas o documento nao tem documento_origem_id",
        )
    linha = db.get(LinhaDocumento, origem_linha_id)
    if not linha:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Linha de origem {origem_linha_id} nao encontrada",
        )
    if linha.documento_id != origem.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Linha de origem nao pertence ao documento de origem",
        )


def _moeda_base(db: Session) -> Moeda:
    m = db.query(Moeda).filter(Moeda.base.is_(True)).first()
    if not m:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Moeda base (MZN) nao configurada",
        )
    return m


def _snapshot_cliente(db: Session, cliente_id: int | None) -> dict:
    if cliente_id is None:
        # fallback: consumidor final
        cf = db.query(Cliente).filter(Cliente.consumidor_final.is_(True)).first()
        if not cf:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Cliente obrigatorio (e consumidor final nao existe)",
            )
        cliente = cf
    else:
        cliente = db.get(Cliente, cliente_id)
        if not cliente:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cliente inexistente")
    if not cliente.ativo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cliente inativo")
    return {
        "cliente_id": cliente.id,
        "cliente_nome": cliente.nome,
        "cliente_nuit": cliente.nuit,
        "cliente_morada": cliente.morada,
    }


def _validar_linha(db: Session, linha: LinhaCreate, data_doc: date) -> tuple[Artigo, Imposto, Unidade]:
    artigo = db.get(Artigo, linha.artigo_id)
    if not artigo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Artigo {linha.artigo_id} inexistente")
    if not artigo.ativo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Artigo {artigo.codigo} inativo")

    imposto = db.get(Imposto, artigo.imposto_id)
    if not imposto or not imposto.ativo:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Imposto do artigo {artigo.codigo} invalido",
        )
    if imposto.vigencia_inicio > data_doc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Imposto {imposto.codigo} ainda nao esta em vigor",
        )
    if imposto.vigencia_fim and imposto.vigencia_fim < data_doc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Imposto {imposto.codigo} expirou em {imposto.vigencia_fim}",
        )

    unidade = db.get(Unidade, artigo.unidade_id)
    if not unidade:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unidade do artigo inexistente")

    return artigo, imposto, unidade


def _calcular_e_snapshot_linha(
    db: Session,
    linha_orm: LinhaDocumento,
    linha_in: LinhaCreate,
    data_doc: date,
    origem: Documento | None = None,
) -> None:
    artigo, imposto, unidade = _validar_linha(db, linha_in, data_doc)
    _validar_linha_origem(db, origem, linha_in.documento_origem_linha_id)

    preco_com_iva = (
        Decimal(linha_in.preco_unitario)
        if linha_in.preco_unitario is not None
        else Decimal(artigo.preco_unitario)
    )

    taxa = Decimal(imposto.percentagem)
    qty_int = int(linha_in.quantidade)
    if qty_int <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Quantidade deve ser >= 1",
        )
    qty_dec = Decimal(qty_int)
    desc_pct = Decimal(linha_in.desconto_percentual)

    # 1) Total bruto (o que o cliente pagaria sem desconto)
    total_bruto = _round_2(preco_com_iva * qty_dec)

    # 2) Desconto da linha
    desc_valor = _round_2(total_bruto * desc_pct / Decimal("100"))
    total_final = _round_2(total_bruto - desc_valor)

    # 3) Separar base e IVA a partir do total final.
    # Garante base + iva == total_final (IVA absorve o arredondamento).
    divisor = Decimal("1") + taxa / Decimal("100")
    base_final = _round_2(total_final / divisor)
    iva = _round_2(total_final - base_final)

    linha_orm.codigo = artigo.codigo
    linha_orm.descricao = artigo.descricao
    linha_orm.unidade = unidade.codigo
    linha_orm.documento_origem_linha_id = linha_in.documento_origem_linha_id
    linha_orm.quantidade = qty_int
    linha_orm.preco_unitario = _round_4(preco_com_iva)  # guarda COM IVA
    linha_orm.desconto_percentual = desc_pct
    linha_orm.taxa_iva = taxa
    linha_orm.base_tributavel = base_final
    linha_orm.valor_iva = iva
    linha_orm.total_linha = total_final


def _recalcular_totais(db: Session, doc: Documento) -> None:
    subtotal = sum((l.base_tributavel for l in doc.linhas), Decimal("0"))
    iva_bruto = sum((l.valor_iva for l in doc.linhas), Decimal("0"))

    if doc.desconto_global_percentual > 0 and subtotal > 0:
        desc_base = _round_2(subtotal * doc.desconto_global_percentual / Decimal("100"))
        base_pos = subtotal - desc_base
        ratio = base_pos / subtotal
        iva_pos = _round_2(iva_bruto * ratio)
    else:
        desc_base = Decimal("0")
        base_pos = subtotal
        iva_pos = iva_bruto

    doc.subtotal = subtotal
    doc.desconto_global_valor = desc_base
    doc.total_iva = iva_pos
    doc.total = base_pos + iva_pos


def _substituir_linhas(
    db: Session,
    doc: Documento,
    linhas_in,
    origem: Documento | None = None,
) -> None:
    requer_origem = origem is not None and doc.tipo_documento in (
        TipoDocumentoFiscal.NC,
        TipoDocumentoFiscal.ND,
    )
    for l in list(doc.linhas):
        db.delete(l)
    db.flush()
    for li in linhas_in:
        if isinstance(li, dict):
            li = LinhaCreate(**li)
        if requer_origem and li.documento_origem_linha_id is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Linhas de {doc.tipo_documento.value} exigem documento_origem_linha_id",
            )
        nova = LinhaDocumento(documento_id=doc.id, artigo_id=li.artigo_id)
        db.add(nova)
        _calcular_e_snapshot_linha(db, nova, li, doc.data_documento, origem=origem)
    db.flush()
    db.refresh(doc)


# ---------------------------------------------------------------- endpoints


@router.get("", response_model=list[DocumentoRead])
def listar(
    tipo: TipoDocumentoFiscal | None = None,
    estado: EstadoDocumento | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    q = db.query(Documento)
    if tipo:
        q = q.filter(Documento.tipo_documento == tipo)
    if estado:
        q = q.filter(Documento.estado == estado)
    return q.order_by(Documento.id.desc()).all()


@router.get("/{doc_id}", response_model=DocumentoRead)
def obter(
    doc_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    return _obter_ou_404(db, doc_id)


@router.post("", response_model=DocumentoRead, status_code=201)
def criar(
    payload: DocumentoCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_faturar),
):
    serie = obter_serie_ativa(db, payload.serie_id, payload.tipo_documento)

    # Validar origem (NC/ND/RC)
    origem = _validar_documento_origem(
        db, payload.tipo_documento, payload.documento_origem_id
    )

    moeda = _moeda_base(db)
    cliente_snap = _snapshot_cliente(db, payload.cliente_id)

    # Para NC/ND/RC herda o cliente da origem (se nao indicado)
    if origem is not None and payload.cliente_id is None:
        cliente_snap = {
            "cliente_id": origem.cliente_id,
            "cliente_nome": origem.cliente_nome,
            "cliente_nuit": origem.cliente_nuit,
            "cliente_morada": origem.cliente_morada,
        }

    doc = Documento(
        tipo_documento=payload.tipo_documento,
        fiscal=_e_fiscal(payload.tipo_documento),
        serie_id=serie.id,
        numero=0,
        numero_formatado="",
        data_documento=payload.data_documento,
        data_vencimento=payload.data_vencimento,
        condicao_pagamento=payload.condicao_pagamento,
        moeda_id=moeda.id,
        taxa_cambio=Decimal("1"),
        estado=EstadoDocumento.RASCUNHO,
        desconto_global_percentual=payload.desconto_global_percentual,
        observacoes=payload.observacoes,
        documento_origem_id=payload.documento_origem_id,
        criado_por_id=user.id,
        **cliente_snap,
    )
    db.add(doc)
    db.flush()

    _substituir_linhas(db, doc, payload.linhas, origem=origem)
    _recalcular_totais(db, doc)
    db.commit()
    db.refresh(doc)

    auditoria.registar(
        db, operacao="criar_documento_rascunho", utilizador=user,
        entidade="documento", entidade_id=doc.id,
        detalhes=f"tipo={doc.tipo_documento.value}",
        ip=request.client.host if request.client else None,
    )
    return doc


@router.patch("/{doc_id}", response_model=DocumentoRead)
def atualizar(
    doc_id: int,
    payload: DocumentoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_faturar),
):
    doc = _obter_ou_404(db, doc_id)
    _garantir_rascunho(doc)

    dados = payload.model_dump(exclude_unset=True)

    if "cliente_id" in dados:
        snap = _snapshot_cliente(db, dados.pop("cliente_id"))
        for k, v in snap.items():
            setattr(doc, k, v)

    if "data_vencimento" in dados:
        doc.data_vencimento = dados.pop("data_vencimento")
    if "condicao_pagamento" in dados:
        doc.condicao_pagamento = dados.pop("condicao_pagamento")
    if "desconto_global_percentual" in dados:
        doc.desconto_global_percentual = dados.pop("desconto_global_percentual")
    if "observacoes" in dados:
        doc.observacoes = dados.pop("observacoes")

    linhas = dados.pop("linhas", None)

    db.flush()

    if linhas is not None:
        origem = None
        if doc.documento_origem_id:
            origem = db.get(Documento, doc.documento_origem_id)
        _substituir_linhas(db, doc, linhas, origem=origem)

    _recalcular_totais(db, doc)
    db.commit()
    db.refresh(doc)

    auditoria.registar(
        db, operacao="atualizar_documento_rascunho", utilizador=user,
        entidade="documento", entidade_id=doc.id,
        ip=request.client.host if request.client else None,
    )
    return doc


@router.delete("/{doc_id}", status_code=204)
def remover_rascunho(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_faturar),
):
    doc = _obter_ou_404(db, doc_id)
    _garantir_rascunho(doc)

    # apaga linhas explicitamente (cascata cobre, mas garante ordem)
    for l in list(doc.linhas):
        db.delete(l)
    db.flush()
    db.delete(doc)
    db.commit()

    auditoria.registar(
        db, operacao="remover_documento_rascunho", utilizador=user,
        entidade="documento", entidade_id=doc_id,
        ip=request.client.host if request.client else None,
    )


@router.post("/{doc_id}/finalizar", response_model=DocumentoRead)
def finalizar(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_faturar),
):
    doc = _obter_ou_404(db, doc_id)
    _garantir_rascunho(doc)

    if not doc.linhas:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Documento sem linhas")

    serie = obter_serie_ativa(db, doc.serie_id, doc.tipo_documento)
    validar_data_nao_anterior(db, serie.id, doc.data_documento)

    # Documentos RC podem ter linhas sem artigo (sao linhas de liquidacao
    # de faturas). Todos os outros tipos exigem artigo.
    if doc.tipo_documento != TipoDocumentoFiscal.RC:
        for linha in doc.linhas:
            if linha.artigo_id is None:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "Linha sem artigo associado",
                )
            db.flush()

    _recalcular_totais(db, doc)

    numero = atribuir_numero(db, serie)

    # Compensacao NC/ND: nao pode exceder o total da origem
    if doc.tipo_documento in (TipoDocumentoFiscal.NC, TipoDocumentoFiscal.ND):
        origem = db.get(Documento, doc.documento_origem_id)
        if origem:
            outros = (
                db.query(Documento)
                .filter(
                    Documento.documento_origem_id == origem.id,
                    Documento.tipo_documento.in_(
                        [TipoDocumentoFiscal.NC, TipoDocumentoFiscal.ND]
                    ),
                    Documento.estado == EstadoDocumento.FINALIZADO,
                    Documento.id != doc.id,
                )
                .all()
            )
            total_compensado = sum((d.total for d in outros), Decimal("0")) + doc.total
            if total_compensado > origem.total:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Compensacao ({total_compensado}) excede o total da origem ({origem.total})",
                )

    # ---- Integridade fiscal (M6) ----
    # A chave RSA tem de existir ANTES de mudarmos o estado do documento.
    # Documentos nao fiscais (COT/PRO/GR) nao recebem hash nem assinatura.
    chave = None
    if settings.SIGNING_ENABLED and doc.fiscal:
        chave = assinatura.criar_ou_obter_ativa(db)

    h = None
    assinatura_b64 = None
    if chave is not None:
        anterior = (
            db.query(Documento)
            .filter(
                Documento.serie_id == serie.id,
                Documento.id != doc.id,
                Documento.fiscal.is_(True),
                Documento.estado.in_(
                    [EstadoDocumento.FINALIZADO, EstadoDocumento.ANULADO]
                ),
            )
            .order_by(Documento.numero.desc())
            .first()
        )
        hash_anterior = anterior.hash if anterior else None

        h = assinatura.calcular_hash(
            tipo=doc.tipo_documento.value,
            serie_prefixo=serie.prefixo,
            numero=numero,
            data_documento=doc.data_documento.isoformat(),
            cliente_nuit=doc.cliente_nuit,
            total=str(doc.total),
            hash_anterior=hash_anterior,
        )
        assinatura_b64 = assinatura.assinar(assinatura.payload_assinado(h), chave)

    # Snapshot de dados bancarios da empresa (para o PDF)
    empresa = db.query(Empresa).order_by(Empresa.id).first()
    if empresa:
        doc.banco = empresa.banco
        doc.nib = empresa.nib
        doc.conta = empresa.conta

    # Um unico UPDATE: estado + numero + hash + assinatura
    doc.numero = numero
    doc.numero_formatado = formatar_numero(serie, numero)
    doc.estado = EstadoDocumento.FINALIZADO
    doc.finalizado_em = utcnow()
    doc.finalizado_por_id = user.id
    if h is not None:
        doc.hash = h
        doc.assinatura = assinatura_b64

    db.commit()
    db.refresh(doc)

    auditoria.registar(
        db, operacao="finalizar_documento", utilizador=user,
        entidade="documento", entidade_id=doc.id,
        detalhes=f"{doc.numero_formatado}",
        ip=request.client.host if request.client else None,
    )
    return doc


@router.delete("/{doc_id}", status_code=204)
def eliminar_rascunho(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
        user: Utilizador = Depends(get_current_user),
):
    doc = db.get(Documento, doc_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Documento nao encontrado")
    
    if doc.estado != EstadoDocumento.RASCUNHO:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "Apenas rascunhos podem ser eliminados. Documentos finalizados devem ser anulados."
        )
    
    db.delete(doc)
    db.commit()
    
    auditoria.registar(
        db, operacao="eliminar_rascunho", utilizador=user,
        entidade="documento", entidade_id=doc_id,
        ip=request.client.host if request.client else None,
    )
    return None

@router.post("/{doc_id}/anular", response_model=DocumentoRead)
def anular(
    doc_id: int,
    payload: DocumentoAnular,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_faturar),
):
    doc = _obter_ou_404(db, doc_id)

    if doc.estado != EstadoDocumento.FINALIZADO:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Documento em estado '{doc.estado.value}' nao pode ser anulado",
        )

    doc.estado = EstadoDocumento.ANULADO
    doc.motivo_anulacao = payload.motivo_anulacao
    doc.anulado_em = utcnow()
    doc.anulado_por_id = user.id
    db.commit()
    db.refresh(doc)

    auditoria.registar(
        db, operacao="anular_documento", utilizador=user,
        entidade="documento", entidade_id=doc.id,
        detalhes=f"{doc.numero_formatado} motivo={payload.motivo_anulacao}",
        ip=request.client.host if request.client else None,
    )
    return doc
@router.get("/{doc_id}/pdf")
def obter_pdf(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_faturar),
):
    doc = _obter_ou_404(db, doc_id)

    if doc.estado == EstadoDocumento.RASCUNHO:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Nao e possivel imprimir rascunhos. Finalize primeiro.",
        )

    empresa = db.query(Empresa).order_by(Empresa.id).first()
    try:
        conteudo = pdf.gerar_pdf_documento(doc, empresa)
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Falha ao gerar PDF: {e}",
        )

    auditoria.registar(
        db, operacao="imprimir_pdf_documento", utilizador=user,
        entidade="documento", entidade_id=doc.id,
        detalhes=doc.numero_formatado or "",
        ip=request.client.host if request.client else None,
    )

    nome = (doc.numero_formatado or "documento").replace(" ", "_").replace("/", "-") + ".pdf"
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{nome}"'},
    )