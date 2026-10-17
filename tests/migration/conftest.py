"""SQLite attached schemas exercise actual tenant_bind/tenant_session routing.

Set MIGRATION_TEST_DATABASE_URL to a dedicated PostgreSQL database whose name
ends in _test to also exercise PostgreSQL DDL, FKs and advisory locks. The test
fixture creates and removes tables/schemas there; never use a real provider DB.
"""
import os
from pathlib import Path

import pytest
from sqlalchemy import event, text
from sqlalchemy.engine import make_url

from app import create_app
from app.extensions import db
from app.models import Organisation, User, Role, Membership, CredentialType
from app.services.tenant import provision_tenant_schema, schema_name_for_organisation

ORG_A = "00000000-0000-0000-0000-000000000001"
ORG_B = "00000000-0000-0000-0000-000000000002"


@pytest.fixture
def application(tmp_path):
    uri = os.environ.get("MIGRATION_TEST_DATABASE_URL")
    if uri and not (make_url(uri).database or "").endswith("_test"):
        raise RuntimeError("MIGRATION_TEST_DATABASE_URL must name a disposable database ending in _test.")
    class Config:
        TESTING = True
        SECRET_KEY = "migration-tests-only"
        SQLALCHEMY_DATABASE_URI = uri or f"sqlite:///{tmp_path / 'main.db'}"
        MIGRATION_STORAGE_ROOT = str(tmp_path / "private")
    app = create_app(Config)
    with app.app_context():
        engine = db.engine
        if engine.dialect.name == "sqlite":
            @event.listens_for(engine, "connect")
            def attach(conn, _):
                conn.execute("PRAGMA foreign_keys=ON")
                for name in ["public", schema_name_for_organisation(ORG_A), schema_name_for_organisation(ORG_B)]:
                    conn.execute(f'ATTACH DATABASE ? AS "{name}"', (str(tmp_path / (name + ".db")),))
            public = [t for t in db.metadata.tables.values() if t.schema == "public"]
            db.metadata.create_all(engine, tables=public)
            for org in [ORG_A, ORG_B]:
                tables = [t for t in db.metadata.tables.values() if t.schema == "tenant"]
                db.metadata.create_all(engine.execution_options(schema_translate_map={"tenant":schema_name_for_organisation(org)}), tables=tables)
        else:
            # Explicitly destructive only in the opt-in disposable test database.
            with engine.begin() as conn:
                for org in [ORG_A, ORG_B]:
                    conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name_for_organisation(org)}" CASCADE'))
                conn.execute(text('DROP SCHEMA public CASCADE'))
                conn.execute(text('CREATE SCHEMA public'))
            public = [t for t in db.metadata.tables.values() if t.schema == "public"]
            db.metadata.create_all(engine, tables=public)
            for org in [ORG_A, ORG_B]:
                provision_tenant_schema(org)
        roles = {r:Role(name=r) for r in ["organisation_admin", "compliance_manager", "staff_member"]}
        db.session.add_all(list(roles.values()))
        db.session.add_all([Organisation(id=ORG_A, legal_name="Fictional Provider A"),
                            Organisation(id=ORG_B, legal_name="Fictional Provider B")])
        users = {}
        for label, org, role in [("admin_a",ORG_A,"organisation_admin"), ("manager",ORG_A,"compliance_manager"),
                                 ("staff",ORG_A,"staff_member"), ("admin_b",ORG_B,"organisation_admin")]:
            user = User(email=label+"@example.test", password_hash="test hash")
            db.session.add(user)
            db.session.flush()
            db.session.add(Membership(user_id=user.id, organisation_id=org, role_record=roles[role]))
            users[label] = user.id
        db.session.add(CredentialType(name="First Aid", has_expiry=True))
        db.session.commit()
    app.test_users = users
    yield app
    with app.app_context():
        db.session.remove()
        if engine.dialect.name == "postgresql":
            with engine.begin() as conn:
                for org in [ORG_A, ORG_B]:
                    conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name_for_organisation(org)}" CASCADE'))
                conn.execute(text('DROP SCHEMA public CASCADE'))
                conn.execute(text('CREATE SCHEMA public'))
        engine.dispose()


@pytest.fixture
def client(application):
    return login(application, "admin_a", ORG_A)


def login(app, user, org):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = app.test_users[user]
        sess["_fresh"] = True
        sess["organisation_id"] = org
        sess["migration_csrf"] = "test-csrf"
    return client


def post(client, url, data=None, **kwargs):
    data = dict(data or {})
    data["csrf_token"] = "test-csrf"
    return client.post(url, data=data, **kwargs)
