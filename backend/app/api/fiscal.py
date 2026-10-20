from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_perfis
from app.core.database import get_db
from app.models.empresa import Empresa
from app.models.ficheiro_exportado import FicheiroExportado, TipoExportacao
from app.models.utilizador import Perfil, Utilizador
from app.services import auditoria, edeclaracao, mapa_iva, saft

router = APIRouter(prefix="/api/fiscal", tags=["fiscal"])

_pode_exportar = require_perfis(Perfil.ADMINISTRADOR, Perfil.CONTABILISTA)

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

EDECL_DIR = UPLOAD_DIR / "edeclaracao"
EDECL_DIR.mkdir(parents=True, exist_ok=True)

SAFT_DIR = UPLOAD_DIR / "saft"
SAFT_DIR.mkdir(parents=True, exist_ok=True)


def _validar_periodo(ano: int, mes: int) -> None:
    if ano < 2000 or ano > 2100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ano fora do intervalo")
    if mes < 1 or mes > 12:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mes deve ser 1-12")


# ============================================================
# e-Declaracao
# ============================================================


@router.post("/edeclaracao/{ano}/{mes}")
def gerar_edeclaracao(
    ano: int,
    mes: int,
    request: Request,
    formato: str = "xlsx",
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_exportar),
):
    _validar_periodo(ano, mes)
    if formato not in ("xml", "xlsx"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Formato deve ser 'xml' ou 'xlsx'",
        )

    docs = edeclaracao.obter_documentos_periodo(db, ano, mes)
    empresa = db.query(Empresa).order_by(Empresa.id).first()

    partes = edeclaracao.gerar_edeclaracao(docs, empresa, ano, mes, formato)

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    registos: list[dict] = []

    for idx, conteudo in enumerate(partes, start=1):
        nome = f"edeclaracao_{ano}-{mes:02d}_{timestamp}_p{idx}.{formato}"
        caminho = EDECL_DIR / nome
        caminho.write_bytes(conteudo)

        reg = FicheiroExportado(
            tipo=TipoExportacao.EDECLARACAO,
            periodo_ano=ano,
            periodo_mes=mes,
            formato=formato,
            caminho=str(caminho.relative_to(UPLOAD_DIR)),
            tamanho_bytes=len(conteudo),
            numero_parte=idx,
            total_partes=len(partes),
            numero_documentos=len(docs),
            criado_por_id=user.id,
        )
        db.add(reg)
        db.flush()
        registos.append(
            {
                "id": reg.id,
                "nome": nome,
                "tamanho_bytes": reg.tamanho_bytes,
                "numero_parte": idx,
                "total_partes": len(partes),
            }
        )

    db.commit()

    auditoria.registar(
        db,
        operacao="gerar_edeclaracao",
        utilizador=user,
        entidade="fiscal",
        entidade_id=None,
        detalhes=f"{ano}-{mes:02d} formato={formato} partes={len(partes)} docs={len(docs)}",
        ip=request.client.host if request.client else None,
    )

    return {
        "periodo": {"ano": ano, "mes": mes},
        "formato": formato,
        "numero_documentos": len(docs),
        "partes": registos,
    }


# ============================================================
# Mapa de IVA
# ============================================================


@router.get("/mapa-iva/{ano}/{mes}")
def obter_mapa_iva(
    ano: int,
    mes: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(_pode_exportar),
):
    _validar_periodo(ano, mes)
    return mapa_iva.calcular_mapa_iva(db, ano, mes)


# ============================================================
# SAF-T (estrutura provisoria, aguarda XSD da AT)
# ============================================================


@router.post("/saft/{ano}/{mes}")
def gerar_saft_endpoint(
    ano: int,
    mes: int,
    request: Request,
    db: Session = Depends(get_db),
    user: Utilizador = Depends(_pode_exportar),
):
    _validar_periodo(ano, mes)
    try:
        conteudo = saft.gerar_saft(db, ano, mes)
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Falha ao gerar SAF-T: {e}",
        )

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    nome = f"saft_{ano}-{mes:02d}_{timestamp}.xml"
    caminho = SAFT_DIR / nome
    caminho.write_bytes(conteudo)

    reg = FicheiroExportado(
        tipo=TipoExportacao.SAFT,
        periodo_ano=ano,
        periodo_mes=mes,
        formato="xml",
        caminho=str(caminho.relative_to(UPLOAD_DIR)),
        tamanho_bytes=len(conteudo),
        numero_parte=1,
        total_partes=1,
        numero_documentos=0,
        criado_por_id=user.id,
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)

    auditoria.registar(
        db,
        operacao="gerar_saft",
        utilizador=user,
        entidade="fiscal",
        entidade_id=None,
        detalhes=f"{ano}-{mes:02d} bytes={len(conteudo)}",
        ip=request.client.host if request.client else None,
    )

    return {
        "periodo": {"ano": ano, "mes": mes},
        "ficheiro_id": reg.id,
        "nome": nome,
        "tamanho_bytes": len(conteudo),
    }


# ============================================================
# Ficheiros exportados
# ============================================================


@router.get("/ficheiros/{ficheiro_id}/download")
def descarregar(
    ficheiro_id: int,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(_pode_exportar),
):
    reg = db.get(FicheiroExportado, ficheiro_id)
    if not reg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ficheiro nao encontrado")
    caminho = UPLOAD_DIR / reg.caminho
    if not caminho.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ficheiro nao existe no disco")
    return FileResponse(
        caminho,
        media_type="application/octet-stream",
        filename=caminho.name,
    )


@router.get("/ficheiros")
def listar_ficheiros(
    tipo: TipoExportacao | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(_pode_exportar),
):
    q = db.query(FicheiroExportado)
    if tipo:
        q = q.filter(FicheiroExportado.tipo == tipo)
    return [
        {
            "id": r.id,
            "tipo": r.tipo.value,
            "periodo_ano": r.periodo_ano,
            "periodo_mes": r.periodo_mes,
            "formato": r.formato,
            "tamanho_bytes": r.tamanho_bytes,
            "numero_parte": r.numero_parte,
            "total_partes": r.total_partes,
            "numero_documentos": r.numero_documentos,
            "criado_em": r.criado_em.isoformat(),
        }
        for r in q.order_by(FicheiroExportado.criado_em.desc()).limit(200).all()
    ]