"""Connected pages render real empty tenant data and preserve role boundaries."""
from sqlalchemy import event
from app.extensions import db
from app.models import User, Organisation, Role, Membership
from app.services.tenant import schema_name_for_organisation

import pytest
from flask_login import UserMixin

from app import create_app, decorators
from app.constants import Roles


class TestConfig:
    TESTING = True
    SECRET_KEY = "frontend-test-only"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class PreviewUser(UserMixin):
    id = "frontend-test-user"
    email = "preview@example.test"


FRONTEND_ORG = "00000000-0000-0000-0000-000000000099"


@pytest.fixture
def app(tmp_path):
    class DatabaseConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'main.db'}"
    application = create_app(DatabaseConfig)
    with application.app_context():
        engine = db.engine
        @event.listens_for(engine, "connect")
        def attach(conn, _):
            for name in ["public", schema_name_for_organisation(FRONTEND_ORG)]:
                conn.execute(f'ATTACH DATABASE ? AS "{name}"', (str(tmp_path / (name + '.db')),))
        db.metadata.create_all(engine.execution_options(schema_translate_map={"tenant":schema_name_for_organisation(FRONTEND_ORG)}))
    yield application
    with application.app_context():
        db.session.remove()
        engine.dispose()


def signed_in_client(app, monkeypatch, role):
    with app.app_context():
        user = User(id=PreviewUser.id,email=PreviewUser.email,password_hash="test-only")
        organisation = Organisation(id=FRONTEND_ORG,legal_name="Provider")
        role_record = Role(name=role)
        db.session.add_all([user,organisation,role_record])
        db.session.flush()
        db.session.add(Membership(user_id=user.id,organisation_id=FRONTEND_ORG,role_id=role_record.id))
        db.session.commit()
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = PreviewUser.id
        session["_fresh"] = True
        session["organisation_id"] = FRONTEND_ORG
    return client


@pytest.mark.parametrize("url", ["/", "/staff/", "/participants/", "/onboarding/",
                                  "/documents/", "/incidents/", "/incidents/new/", "/my-compliance/"])
def test_frontend_requires_login(app, url):
    response = app.test_client().get(url)
    assert response.status_code == 302
    assert "/auth/login" in response.location


@pytest.mark.parametrize("role, paths", [
    (Roles.ORGANISATION_ADMIN, ["/", "/staff/", "/participants/", "/onboarding/", "/documents/", "/incidents/", "/incidents/new/", "/my-compliance/"]),
    (Roles.COMPLIANCE_MANAGER, ["/", "/staff/", "/participants/", "/documents/", "/incidents/", "/incidents/new/", "/my-compliance/"]),
    (Roles.STAFF_MEMBER, ["/incidents/", "/incidents/new/", "/my-compliance/"]),
])
def test_empty_pages_render_without_fictional_records(app, monkeypatch, role, paths):
    client = signed_in_client(app, monkeypatch, role)
    for url in paths:
        response = client.get(url)
        assert response.status_code == 200, url
        html = response.get_data(as_text=True)
        assert 'method="post" action="/auth/logout"' in html
        assert "Brightwater" not in html
        assert "Fictional example data" not in html
        assert "Douglas Okafor" not in html
        assert client.get(url + "?example=1").get_data(as_text=True) == html


def test_worker_import_has_no_fake_result(app, monkeypatch):
    html = signed_in_client(app, monkeypatch, Roles.ORGANISATION_ADMIN).get("/staff/").get_data(as_text=True)
    assert "No workers yet" in html
    assert '/migration/upload?record_type=staff' in html
    assert "T. Alvarez" not in html
    assert "Import workers</a>" in html


def test_setup_has_no_sample_company_or_assessed_requirements(app, monkeypatch):
    html = signed_in_client(app, monkeypatch, Roles.ORGANISATION_ADMIN).get("/onboarding/").get_data(as_text=True)
    assert "Brightwater" not in html
    assert "Not assessed" in html
    assert "2026-09-27" not in html


@pytest.mark.parametrize("role, path", [
    (Roles.STAFF_MEMBER, "/staff/"), (Roles.STAFF_MEMBER, "/participants/"),
    (Roles.STAFF_MEMBER, "/documents/"), (Roles.COMPLIANCE_MANAGER, "/onboarding/"),
])
def test_existing_role_boundaries(app, monkeypatch, role, path):
    assert signed_in_client(app, monkeypatch, role).get(path).status_code == 403


def test_old_example_routes_are_gone(app, monkeypatch):
    client = signed_in_client(app, monkeypatch, Roles.ORGANISATION_ADMIN)
    for path in ["/staff/examples/daniel-hughes/", "/participants/examples/p-1042/",
                 "/documents/examples/example/", "/incidents/examples/new/"]:
        assert client.get(path).status_code == 404


def test_existing_authentication_forms_and_logout(app, monkeypatch):
    assert app.test_client().get("/auth/login").status_code == 200
    assert app.test_client().get("/auth/register").status_code == 200
    client = signed_in_client(app, monkeypatch, Roles.ORGANISATION_ADMIN)
    assert client.post("/auth/logout").status_code == 302
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_all_templates_compile(app):
    for template in app.jinja_env.list_templates():
        app.jinja_env.get_template(template)
