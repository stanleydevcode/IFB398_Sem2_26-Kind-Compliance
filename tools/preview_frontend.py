r"""Render the frontend to a local, read-only preview without PostgreSQL.

Run: .\kind\Scripts\python.exe tools\preview_frontend.py
The HTTP server serves rendered HTML only. It never exposes a Flask session,
accepts a form POST or uses your configured database. The project's database URL is
overridden with disposable SQLite files in a temporary directory.
"""
import argparse
import sys
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlsplit
import mimetypes

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.constants import Roles
from sqlalchemy import event
from app.extensions import db
from app.models import User, Organisation, Role, Membership
from app.services.tenant import schema_name_for_organisation


class PreviewConfig:
    TESTING = True
    SECRET_KEY = "isolated-static-frontend-preview"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def render_pages():
    """Render empty live views against disposable local test tables."""
    with TemporaryDirectory(prefix="kind-frontend-preview-") as temporary:
        folder = Path(temporary)
        organisation_id = "00000000-0000-0000-0000-000000000099"
        tenant_schema = schema_name_for_organisation(organisation_id)
        class LocalConfig(PreviewConfig):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{folder / 'main.db'}"
        app = create_app(LocalConfig)
        with app.app_context():
            engine = db.engine
            @event.listens_for(engine, "connect")
            def attach(connection, _):
                for schema in ["public", tenant_schema]:
                    connection.execute(f'ATTACH DATABASE ? AS "{schema}"', (str(folder / (schema + '.db')),))
            db.metadata.create_all(engine.execution_options(schema_translate_map={"tenant":tenant_schema}))
            db.session.add(Organisation(id=organisation_id, legal_name="Design preview"))
            for label, role in [("admin", Roles.ORGANISATION_ADMIN), ("manager", Roles.COMPLIANCE_MANAGER), ("staff", Roles.STAFF_MEMBER)]:
                user = User(id=label, email=label+"@example.test", password_hash="preview-disabled")
                role_record = Role(name=role)
                db.session.add_all([user, role_record])
                db.session.flush()
                db.session.add(Membership(user_id=user.id, organisation_id=organisation_id, role_id=role_record.id))
            db.session.commit()
        pages = {}
        try:
            for role in ["admin", "manager", "staff"]:
                client = app.test_client()
                with client.session_transaction() as session:
                    session.update(_user_id=role, _fresh=True, organisation_id=organisation_id)
                urls = ["/incidents/", "/incidents/new/", "/my-compliance/", "/participants/assigned", "/participants/assigned?tab=notes"]
                if role != "staff":
                    urls += ["/", "/staff/", "/staff/?tab=verify", "/participants/", "/participants/?tab=notes",
                             "/documents/", "/documents/?tab=missing", "/documents/?tab=pending", "/documents/?tab=requirements",
                             "/documents/upload", "/risks/", "/migration/", "/migration/upload", "/migration/documents"]
                if role == "admin":
                    urls += ["/onboarding/", "/staff/?tab=logins"]
                for url in urls:
                    response = client.get(url)
                    if response.status_code != 200:
                        raise RuntimeError(f"Preview rendering failed: {role} {url} ({response.status_code})")
                    html = response.get_data(as_text=True)
                    html = html.replace('method="post" action="/auth/logout"', 'action="/preview/"')
                    html = html.replace('Sign out</button>', 'Preview roles</button>')
                    pages[(role, url)] = html.encode("utf-8")
        finally:
            with app.app_context():
                db.session.remove()
                engine.dispose()
        return pages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5505)
    parser.add_argument("--check", action="store_true", help="Render all pages and exit; do not start a server")
    args = parser.parse_args()
    pages = render_pages()
    print(f"Rendered {len(pages)} frontend pages. Disposable SQLite preview only; configured database was not accessed.", flush=True)
    if args.check:
        return

    class Handler(BaseHTTPRequestHandler):
        def send(self, status, data, content_type="text/html; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            url = urlsplit(self.path)
            query = parse_qs(url.query)
            if url.path == "/preview/":
                selected = query.get("role", [None])[0]
                if selected in ("admin", "manager", "staff"):
                    self.send_response(303)
                    self.send_header("Set-Cookie", f"frontend_preview_role={selected}; Path=/; SameSite=Strict; HttpOnly")
                    self.send_header("Location", "/my-compliance/" if selected == "staff" else "/staff/")
                    self.end_headers()
                    return
                self.send(200, b'''<!doctype html><meta charset="utf-8"><title>Frontend preview</title>
<main style="font:18px system-ui;max-width:700px;margin:60px auto;padding:20px">
<h1>Kind Compliance frontend preview</h1><p>Static empty-state pages. No PostgreSQL, real accounts, uploads or saves.</p>
<p><a href="?role=admin">Preview Administrator</a></p><p><a href="?role=manager">Preview Compliance Manager</a></p>
<p><a href="?role=staff">Preview Staff Member</a></p>
<p>Forms are interface drafts. Refresh discards in-page changes.</p></main>''')
                return
            if url.path.startswith("/static/"):
                static_root = (ROOT / "app" / "static").resolve()
                target = (static_root / url.path[len("/static/"):]).resolve()
                if not target.is_relative_to(static_root) or not target.is_file():
                    self.send(404, b"Asset not found")
                    return
                self.send(200, target.read_bytes(), mimetypes.guess_type(target.name)[0] or "application/octet-stream")
                return
            cookie = SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            role = cookie.get("frontend_preview_role")
            role_name = role.value if role and role.value in ("admin", "manager", "staff") else "admin"
            key = url.path + ("?" + url.query if url.query else "")
            data = pages.get((role_name, key))
            if data is None:
                self.send(404, b'<p>This page is not included in the frontend preview. <a href="/preview/">Choose a role</a></p>')
                return
            self.send(200, data)

        def do_POST(self):
            self.send(405, b"Read-only frontend preview. No records saved.", "text/plain; charset=utf-8")

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://127.0.0.1:{args.port}/preview/ (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
