"""The integrated frontend stays empty until backend records are available."""
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
    assert 'id="import-modal"' in html
    assert "T. Alvarez" not in html
    assert "12" not in html.split('id="import-modal"', 1)[1]
    assert "Review import</button>" in html


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
