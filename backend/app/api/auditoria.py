from datetime import date, datetime, time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import require_perfis
from app.core.database import get_db
from app.models.auditoria import Auditoria
from app.models.utilizador import Perfil, Utilizador
from app.schemas.auditoria import AuditoriaRead

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])

# Apenas Administradores e Auditores podem ver o log
_pode_ver_auditoria = require_perfis(Perfil.ADMINISTRADOR, Perfil.AUDITOR)


@router.get("", response_model=list[AuditoriaRead])
def listar_auditoria(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    operacao: str | None = None,
    pesquisa: str | None = None,
    db: Session = Depends(get_db),
    _: Utilizador = Depends(_pode_ver_auditoria),
):
    q = db.query(Auditoria, Utilizador.nome_completo).outerjoin(
        Utilizador, Auditoria.utilizador_id == Utilizador.id
    )

    if data_inicio:
        dt_inicio = datetime.combine(data_inicio, time.min)
        q = q.filter(Auditoria.criado_em >= dt_inicio)

    if data_fim:
        dt_fim = datetime.combine(data_fim, time.max)
        q = q.filter(Auditoria.criado_em <= dt_fim)

    if operacao:
        q = q.filter(Auditoria.operacao == operacao)

    if pesquisa:
        filtro = f"%{pesquisa}%"
        q = q.filter(
            or_(
                Auditoria.detalhes.ilike(filtro),
                Auditoria.entidade.ilike(filtro),
                Utilizador.nome_completo.ilike(filtro),
            )
        )

    resultados = q.order_by(Auditoria.criado_em.desc()).limit(500).all()

    # Constrói explicitamente em vez de model_validate,
    # para incluir o nome do utilizador vindo do JOIN
    logs: list[AuditoriaRead] = []
    for audit, nome_util in resultados:
        logs.append(
            AuditoriaRead(
                id=audit.id,
                operacao=audit.operacao,
                utilizador_id=audit.utilizador_id,
                utilizador_nome=nome_util or "Sistema",
                entidade=audit.entidade,
                entidade_id=audit.entidade_id,
                detalhes=audit.detalhes,
                ip=audit.ip,
                criado_em=audit.criado_em,
            )
        )

    return logs