from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_columns()


# create_all() never adds columns to tables that already exist (e.g. the live
# Neon database from v2), so new columns are added idempotently here.
_NEW_COLUMNS = {
    "scenarios": [("is_custom", "BOOLEAN DEFAULT FALSE"), ("created_by", "VARCHAR(200)")],
    "test_runs": [
        ("workspace_id", "VARCHAR(80)"),
        ("agent_kind", "VARCHAR(20) DEFAULT 'mock'"),
        ("model", "VARCHAR(120)"),
    ],
}


def _migrate_columns() -> None:
    from sqlalchemy import text

    is_pg = not settings.database_url.startswith("sqlite")
    with engine.begin() as conn:
        for table, cols in _NEW_COLUMNS.items():
            for name, ddl in cols:
                if is_pg:
                    stmt = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {name} {ddl}'
                else:
                    stmt = f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"
                try:
                    conn.execute(text(stmt))
                except Exception:
                    # SQLite raises if the column already exists; Postgres
                    # IF NOT EXISTS never does. Either way: already migrated.
                    pass
