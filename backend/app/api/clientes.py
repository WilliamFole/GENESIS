from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_perfis
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.documento import Documento, EstadoDocumento, TipoDocumentoFiscal
from app.models.utilizador import Perfil, Utilizador
from app.schemas.cliente import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    ContaCorrente,
    MovimentoContaCorrente,
)
from app.services import auditoria

router = APIRouter(prefix="/api/clientes", tags=["clientes"])

_pode_escrever = require_perfis(Perfil.ADMINISTRADOR, Perfil.FATURACAO, Perfil.CONTABILISTA)


def _obter_ou_404(db: Session, cliente_id: int) -> Cliente:
    c = db.get(Cliente, cliente_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado")
    return c


def _proximo_numero(db: Session) -> int:
    ultimo = db.query(func.max(Cliente.numero)).scalar() or 0
    return int(ultimo) + 1


@router.get("", response_model=list[ClienteRead])
def listar(
    q: str | None = None,
    apenas_ativos: bool = False,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    query = db.query(Cliente)
    if apenas_ativos:
        query = query.filter(Cliente.ativo.is_(True))
    if q:
        filtro = f"%{q}%"
        query = query.filter(
            (Cliente.nome.ilike(filtro)) | (Cliente.nuit.ilike(filtro))
        )
    return query.order_by(Cliente.nome).all()


@router.get("/{cliente_id}", response_model=ClienteRead)
def obter(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    return _obter_ou_404(db, cliente_id)


@router.post("", response_model=ClienteRead, status_code=201)
def criar(
    payload: ClienteCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_escrever),
):
    existe = db.query(Cliente).filter(Cliente.nuit == payload.nuit).first()
    if existe:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Ja existe um cliente com este NUIT"
        )

    numero = _proximo_numero(db)
    cliente = Cliente(numero=numero, **payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    auditoria.registar(
        db, operacao="criar_cliente", utilizador=user,
        entidade="cliente", entidade_id=cliente.id,
        detalhes=f"numero=CLI{numero:05d} nuit={cliente.nuit}",
        ip=request.client.host if request.client else None,
    )
    return cliente


@router.patch("/{cliente_id}", response_model=ClienteRead)
def atualizar(
    cliente_id: int,
    payload: ClienteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_escrever),
):
    cliente = _obter_ou_404(db, cliente_id)
    dados = payload.model_dump(exclude_unset=True)

    # NUIT duplicado noutro cliente?
    if "nuit" in dados and dados["nuit"] != cliente.nuit:
        existe = (
            db.query(Cliente)
            .filter(Cliente.nuit == dados["nuit"], Cliente.id != cliente.id)
            .first()
        )
        if existe:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Ja existe outro cliente com este NUIT",
            )

    # Consumidor final: nome nao pode ser alterado
    if cliente.consumidor_final and "nome" in dados and dados["nome"] != cliente.nome:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "O nome do cliente Consumidor Final nao pode ser alterado",
        )

    for k, v in dados.items():
        setattr(cliente, k, v)
    db.commit()
    db.refresh(cliente)

    auditoria.registar(
        db, operacao="atualizar_cliente", utilizador=user,
        entidade="cliente", entidade_id=cliente.id,
        ip=request.client.host if request.client else None,
    )
    return cliente


@router.delete("/{cliente_id}", status_code=204)
def eliminar(
    cliente_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_escrever),
):
    cliente = _obter_ou_404(db, cliente_id)

    if cliente.consumidor_final:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "O cliente Consumidor Final nao pode ser eliminado",
        )

    tem_docs = (
        db.query(Documento)
        .filter(Documento.cliente_id == cliente.id)
        .first()
    )
    if tem_docs:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cliente tem documentos emitidos e nao pode ser eliminado. Inative-o.",
        )

    db.delete(cliente)
    db.commit()

    auditoria.registar(
        db, operacao="eliminar_cliente", utilizador=user,
        entidade="cliente", entidade_id=cliente_id,
        ip=request.client.host if request.client else None,
    )
    return None


@router.get("/{cliente_id}/conta-corrente", response_model=ContaCorrente)
def conta_corrente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(get_current_user),
):
    c = _obter_ou_404(db, cliente_id)
    movs: list[dict] = []

    docs = (
        db.query(Documento)
        .filter(
            Documento.cliente_id == c.id,
            Documento.estado == EstadoDocumento.FINALIZADO,
            Documento.tipo_documento.in_([
                TipoDocumentoFiscal.FT,
                TipoDocumentoFiscal.VD,
                TipoDocumentoFiscal.FS,
            ]),
        )
        .all()
    )
    for d in docs:
        movs.append({
            "data": d.data_documento,
            "tipo": d.tipo_documento.value,
            "numero": d.numero_formatado,
            "descricao": f"{d.tipo_documento.value} emitida",
            "debito": d.total,
            "credito": Decimal("0"),
        })

    for d in db.query(Documento).filter(
        Documento.cliente_id == c.id,
        Documento.estado == EstadoDocumento.FINALIZADO,
        Documento.tipo_documento == TipoDocumentoFiscal.NC,
    ).all():
        movs.append({
            "data": d.data_documento,
            "tipo": "NC",
            "numero": d.numero_formatado,
            "descricao": "Nota de credito",
            "debito": Decimal("0"),
            "credito": d.total,
        })

    for d in db.query(Documento).filter(
        Documento.cliente_id == c.id,
        Documento.estado == EstadoDocumento.FINALIZADO,
        Documento.tipo_documento == TipoDocumentoFiscal.RC,
    ).all():
        movs.append({
            "data": d.data_documento,
            "tipo": "RC",
            "numero": d.numero_formatado,
            "descricao": "Recibo",
            "debito": Decimal("0"),
            "credito": d.total,
        })

    movs.sort(key=lambda m: (m["data"], m["numero"]))
    saldo = Decimal("0")
    movimentos: list[MovimentoContaCorrente] = []
    for m in movs:
        saldo = saldo + m["debito"] - m["credito"]
        movimentos.append(MovimentoContaCorrente(
            data=m["data"],
            documento_tipo=m["tipo"],
            documento_numero=m["numero"],
            descricao=m["descricao"],
            debito=m["debito"],
            credito=m["credito"],
            saldo=saldo,
        ))

    return ContaCorrente(
        cliente_id=c.id,
        cliente_nome=c.nome,
        saldo=saldo,
        movimentos=movimentos,
    )