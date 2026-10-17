import re
from contextlib import contextmanager

from flask import session
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.extensions import db

TENANT_SCHEMA_TOKEN = "tenant"

def schema_name_for_organisation(organisation_id: str) -> str:
    # UUID-safe / identifier-safe schema name.
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", organisation_id)
    return f"org_{safe}".lower()

def tenant_bind(organisation_id: str):
    schema_name = schema_name_for_organisation(organisation_id)
    return db.engine.execution_options(
        schema_translate_map={TENANT_SCHEMA_TOKEN: schema_name}
    )

@contextmanager
def tenant_session(organisation_id=None):
    organisation_id = organisation_id or session.get("organisation_id")
    if not organisation_id:
        raise RuntimeError("No active organisation in session.")

    Session = sessionmaker(bind=tenant_bind(organisation_id), expire_on_commit=False)
    tenant_db = Session()
    try:
        yield tenant_db
        tenant_db.commit()
    except Exception:
        tenant_db.rollback()
        raise
    finally:
        tenant_db.close()

def provision_tenant_schema(organisation_id: str):
    schema_name = schema_name_for_organisation(organisation_id)

    tenant_tables = [
        table
        for table in db.metadata.tables.values()
        if table.schema == TENANT_SCHEMA_TOKEN
    ]

    with db.engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        translated = conn.execution_options(
            schema_translate_map={TENANT_SCHEMA_TOKEN: schema_name}
        )
        db.metadata.create_all(bind=translated, tables=tenant_tables)
