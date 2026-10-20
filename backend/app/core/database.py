from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass

 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


APEND_ONLY_TRIGGERS = [
    "CREATE TRIGGER IF NOT EXISTS auditoria_no_update "
    "BEFORE UPDATE ON auditoria BEGIN "
    "SELECT RAISE(ABORT, 'auditoria e append-only'); END;",
    "CREATE TRIGGER IF NOT EXISTS auditoria_no_delete "
    "BEFORE DELETE ON auditoria BEGIN "
    "SELECT RAISE(ABORT, 'auditoria e append-only'); END;",
]

# Documentos: UPDATE apenas em rascunho.
# Em FINALIZADO, so a transicao para ANULADO e permitida.
# Em ANULADO, nada se altera.
# DELETE so em rascunho.
DOCUMENTO_TRIGGERS = [
    "CREATE TRIGGER IF NOT EXISTS docs_no_update_finalizado "
    "BEFORE UPDATE ON documentos "
    "WHEN LOWER(OLD.estado) = 'finalizado' AND LOWER(NEW.estado) <> 'anulado' "
    "BEGIN "
    "SELECT RAISE(ABORT, 'documento finalizado nao pode ser alterado'); END;",
    "CREATE TRIGGER IF NOT EXISTS docs_no_update_anulado "
    "BEFORE UPDATE ON documentos "
    "WHEN LOWER(OLD.estado) = 'anulado' "
    "BEGIN "
    "SELECT RAISE(ABORT, 'documento anulado nao pode ser alterado'); END;",
    "CREATE TRIGGER IF NOT EXISTS docs_no_delete "
    "BEFORE DELETE ON documentos "
    "WHEN LOWER(OLD.estado) <> 'rascunho' "
    "BEGIN "
    "SELECT RAISE(ABORT, 'documento emitido nao pode ser eliminado'); END;",
]


def aplicar_triggers_append_only() -> None:
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        for t in APEND_ONLY_TRIGGERS:
            conn.execute(text(t))


def aplicar_triggers_documentos() -> None:
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        for t in DOCUMENTO_TRIGGERS:
            conn.execute(text(t))