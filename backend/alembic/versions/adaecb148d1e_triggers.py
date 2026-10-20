"""triggers

Revision ID: adaecb148d1e
Revises: c1ec75cda8eb
Create Date: ...

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "adaecb148d1e"
down_revision = "c1ec75cda8eb"
branch_labels = None
depends_on = None


TRIGGERS = [
    # Auditoria: append-only
    "CREATE TRIGGER IF NOT EXISTS auditoria_no_update "
    "BEFORE UPDATE ON auditoria BEGIN "
    "SELECT RAISE(ABORT, 'auditoria e append-only'); END;",
    "CREATE TRIGGER IF NOT EXISTS auditoria_no_delete "
    "BEFORE DELETE ON auditoria BEGIN "
    "SELECT RAISE(ABORT, 'auditoria e append-only'); END;",
    # Documentos: imutabilidade apos finalizar
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


def upgrade() -> None:
    for t in TRIGGERS:
        op.execute(t)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS auditoria_no_update;")
    op.execute("DROP TRIGGER IF EXISTS auditoria_no_delete;")
    op.execute("DROP TRIGGER IF EXISTS docs_no_update_finalizado;")
    op.execute("DROP TRIGGER IF EXISTS docs_no_update_anulado;")
    op.execute("DROP TRIGGER IF EXISTS docs_no_delete;")