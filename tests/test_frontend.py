"""Check the new templates without touching the local PostgreSQL database."""
from types import SimpleNamespace

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


@pytest.fixture
def app():
    return create_app(TestConfig)


def signed_in_client(app, monkeypatch, role):
    monkeypatch.setattr(app.login_manager, "_user_callback", lambda user_id: PreviewUser())
    monkeypatch.setattr(decorators, "current_membership", lambda: SimpleNamespace(role=role))
    client = app.test_client()
    with client.session_transaction() as session:
        session["_user_id"] = PreviewUser.id
        session["_fresh"] = True
    return client


def test_workers_still_requires_login(app):
    response = app.test_client().get("/staff/")
    assert response.status_code == 302
    assert "/auth/login" in response.location


@pytest.mark.parametrize("role", [Roles.ORGANISATION_ADMIN, Roles.COMPLIANCE_MANAGER])
def test_worker_shell_and_admin_controls(app, monkeypatch, role):
    html = signed_in_client(app, monkeypatch, role).get("/staff/").get_data(as_text=True)
    assert "No workers yet" in html
    assert 'aria-current="page">Workers' in html
    assert 'method="post" action="/auth/logout"' in html
    assert ('id="import-modal"' in html) == (role == Roles.ORGANISATION_ADMIN)
    assert ('id="pane-logins"' in html) == (role == Roles.ORGANISATION_ADMIN)
    assert "11 workers imported" not in html


def test_workers_still_blocks_staff(app, monkeypatch):
    assert signed_in_client(app, monkeypatch, Roles.STAFF_MEMBER).get("/staff/").status_code == 403


@pytest.mark.parametrize("url, fields", [
    ("/auth/login", ["email", "password"]),
    ("/auth/register", ["organisation_name", "email", "password", "confirm_password"]),
])
def test_existing_auth_forms_render(app, url, fields):
    response = app.test_client().get(url)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for field in fields:
        assert f'name="{field}"' in html


def test_existing_logout_clears_session(app, monkeypatch):
    client = signed_in_client(app, monkeypatch, Roles.ORGANISATION_ADMIN)
    response = client.post("/auth/logout")
    assert response.status_code == 302
    assert response.location.endswith("/auth/login")
    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_all_existing_templates_compile(app):
    for template in app.jinja_env.list_templates():
        app.jinja_env.get_template(template)
