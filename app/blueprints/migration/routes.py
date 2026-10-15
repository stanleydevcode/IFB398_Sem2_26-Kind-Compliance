"""Manager-only migration workspace. All data access uses the active tenant bind."""
import csv
import hashlib
import hmac
import io
import json
import secrets
from collections import Counter
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template,
                   request, send_file, session, url_for)
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app import decorators
from app.models import Document, DocumentVersion, CredentialType, OrganisationRequirement
from app.models.migration import MigrationJob, MigrationRow, MigrationAttachment, MigrationChange
from app.services.permissions import can
from app.services.tenant import tenant_session
from app.services.migration import storage
from app.services.migration.definitions import DEFINITIONS, LABELS
from app.services.migration.reader import MigrationError, read_table
from app.services.migration.engine import (MODELS, apply_mapping, approve_rows, edit_row, audit,
                                           lock_imports, label, snapshot)
from app.services.migration.documents import upload_document, review_document, date_condition

bp = Blueprint("migration", __name__, url_prefix="/migration")


def token():
    if "migration_csrf" not in session:
        session["migration_csrf"] = secrets.token_urlsafe(32)
    return session["migration_csrf"]


@bp.before_request
def authorise():
    request.max_content_length = 11 * 1024 * 1024
    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()
    membership = decorators.current_membership()
    if not membership or not can(membership.role, "run_migration") or not membership.organisation.is_active:
        abort(403)
    g.migration_org = membership.organisation_id
    if request.method == "POST":
        supplied = request.form.get("csrf_token", "")
        if not supplied or not hmac.compare_digest(supplied, token()):
            abort(400, description="Your migration form expired. Reload the page and try again.")


@bp.context_processor
def context():
    return {"migration_csrf": token, "migration_labels": LABELS, "date_condition": date_condition}


@bp.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@bp.errorhandler(MigrationError)
def invalid(error):
    return render_template("migration/error.html", message=str(error)), 400


@bp.errorhandler(SQLAlchemyError)
def database_error(error):
    # Avoid logging SQL bound parameters containing participant information.
    current_app.logger.error("Migration database operation failed (%s)", type(error).__name__)
    return render_template("migration/error.html", message=(
        "The database operation could not complete and was rolled back. If this is the first run, "
        "run the migration-init command in docs/data-migration/README.md. Otherwise reload and retry; "
        "ask the developer to check database connectivity or a concurrent change.")), 409


def tenant_view(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        with tenant_session(g.migration_org) as tenant:
            g.migration_db = tenant
            if request.method == "POST":
                lock_imports(tenant, g.migration_org)
            return view(*args, **kwargs)
    return wrapped


def job_or_404(job_id):
    job = g.migration_db.get(MigrationJob, job_id)
    if job is None:
        abort(404)
    return job


def row_or_404(job, row_id):
    row = next((r for r in job.rows if r.id == row_id), None)
    if row is None:
        abort(404)
    return row


def revision(row):
    return hashlib.sha256(json.dumps([row.data, row.decision, row.status, row.target_id,
                                     row.decision_reason], sort_keys=True).encode()).hexdigest()


@bp.get("/")
@tenant_view
def index():
    jobs = g.migration_db.scalars(select(MigrationJob).order_by(MigrationJob.created_at.desc()).limit(100)).all()
    return render_template("migration/index.html", jobs=jobs, counts=lambda j: Counter(r.status for r in j.rows))


@bp.route("/upload", methods=["GET", "POST"])
@tenant_view
def upload():
    if request.method == "POST":
        kind = request.form.get("record_type")
        system = request.form.get("source_system", "").strip()
        if kind not in DEFINITIONS or not system or len(system) > 100:
            raise MigrationError("Choose a record type and source system up to 100 characters.")
        filename, data = storage.receive(request.files.get("file"))
        headers, records = read_table(data, filename)
        key, digest = storage.save(g.migration_org, data)
        try:
            job = MigrationJob(record_type=kind, source_system=system, filename=filename,
                               source_key=key, source_sha256=digest, uploaded_by=current_user.id, headers=headers)
            g.migration_db.add(job)
            g.migration_db.flush()
            for number, raw in records:
                g.migration_db.add(MigrationRow(job_id=job.id, row_number=number, raw_data=raw))
            audit(g.migration_db, current_user.id, "migration.uploaded", "migration_job", job.id,
                  {"source_sha256": digest, "rows": len(records)})
            g.migration_db.commit()
        except Exception:
            storage.resolve(g.migration_org, key).unlink(missing_ok=True)
            raise
        return redirect(url_for("migration.mapping", job_id=job.id))
    return render_template("migration/upload.html")


@bp.route("/<job_id>/mapping", methods=["GET", "POST"])
@tenant_view
def mapping(job_id):
    job = job_or_404(job_id)
    if job.status != "mapping":
        return redirect(url_for("migration.preview", job_id=job.id))
    fields = DEFINITIONS[job.record_type]
    if request.method == "POST":
        mapping = {key: request.form.get("map_" + key) for key in fields if request.form.get("map_" + key)}
        apply_mapping(g.migration_db, job, mapping, request.form.get("date_format", "iso"), current_user.id)
        return redirect(url_for("migration.preview", job_id=job.id))
    suggestions = {key: next((h for h in job.headers if h.lower().replace(" ", "_") == key), "") for key in fields}
    return render_template("migration/mapping.html", job=job, fields=fields, suggestions=suggestions)


@bp.get("/<job_id>/preview")
@tenant_view
def preview(job_id):
    job = job_or_404(job_id)
    if job.status == "mapping":
        return redirect(url_for("migration.mapping", job_id=job.id))
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        abort(400)
    state = request.args.get("state", "")
    rows = [r for r in job.rows if not state or r.status == state]
    return render_template("migration/preview.html", job=job, counts=Counter(r.status for r in job.rows),
                           rows=rows[(page-1)*50:page*50], page=page, pages=(len(rows)+49)//50, state=state)


@bp.route("/<job_id>/rows/<row_id>", methods=["GET", "POST"])
@tenant_view
def row_review(job_id, row_id):
    job = job_or_404(job_id)
    row = row_or_404(job, row_id)
    if request.method == "POST":
        if request.form.get("revision") != revision(row):
            raise MigrationError("This row changed in another window. Reload and review the latest values.")
        data = {key: request.form.get("field_" + key, "") for key in DEFINITIONS[job.record_type]}
        edit_row(g.migration_db, row, data, request.form.get("decision", "create"),
                 request.form.get("target_id", ""), request.form.get("reason", "").strip(), current_user.id)
        return redirect(url_for("migration.preview", job_id=job.id))
    candidates = []
    for item in row.candidates:
        record = g.migration_db.get(MODELS[job.record_type], item["id"])
        if record:
            candidates.append({"id": record.id, "label": label(record), "values": snapshot(record)})
    changes = g.migration_db.scalars(select(MigrationChange).filter_by(row_id=row.id)).all()
    return render_template("migration/row.html", job=job, row=row, fields=DEFINITIONS[job.record_type],
                           revision=revision(row), candidates=candidates, changes=changes)


@bp.post("/<job_id>/approve")
@tenant_view
def approve(job_id):
    job = job_or_404(job_id)
    count = approve_rows(g.migration_db, job, request.form.getlist("rows"), current_user.id,
                         request.form.get("signoff") == "yes")
    flash(f"{count} record(s) approved and imported. Unresolved rows remain in the review queue.", "success")
    return redirect(url_for("migration.preview", job_id=job.id))


@bp.post("/<job_id>/cancel")
@tenant_view
def cancel(job_id):
    job = job_or_404(job_id)
    if any(r.status == "imported" for r in job.rows):
        raise MigrationError("Imported rows remain live. Skip unresolved rows individually; cancellation is not an undo.")
    job.status = "cancelled"
    audit(g.migration_db, current_user.id, "migration.cancelled", "migration_job", job.id)
    return redirect(url_for("migration.index"))


def csv_response(rows, name):
    def safe(value):
        value = str(value if value is not None else "")
        return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")) else value
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerows([[safe(v) for v in row] for row in rows])
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")), mimetype="text/csv",
                     as_attachment=True, download_name=name)


@bp.get("/templates/<kind>.csv")
def template(kind):
    if kind not in DEFINITIONS:
        abort(404)
    return csv_response([list(DEFINITIONS[kind])], f"{kind}_template.csv")


@bp.get("/<job_id>/reconciliation.csv")
@tenant_view
def reconciliation(job_id):
    job = job_or_404(job_id)
    rows = [["source_row", "legacy_reference", "state", "decision", "destination_id", "errors", "warnings", "reviewer", "approved_at"]]
    rows += [[r.row_number, r.data.get("source_reference", ""), r.status, r.decision, r.destination_id,
              "; ".join(r.errors), "; ".join(r.warnings), r.approved_by, r.approved_at] for r in job.rows]
    return csv_response(rows, f"migration_{job.id}_reconciliation.csv")


@bp.get("/<job_id>/original")
@tenant_view
def original(job_id):
    job = job_or_404(job_id)
    return send_file(storage.verified_bytes(g.migration_org, job.source_key, job.source_sha256),
                     as_attachment=True, download_name=job.filename, mimetype="application/octet-stream")


@bp.get("/records/<kind>")
@tenant_view
def records(kind):
    if kind not in MODELS:
        abort(404)
    query = select(MODELS[kind]).order_by(MODELS[kind].created_at.desc()).limit(200)
    if kind in {"incident", "complaint"}:
        query = query.where(MODELS[kind].case_type == kind)
    items = [{"id": x.id, "label": label(x), "values": snapshot(x)} for x in g.migration_db.scalars(query)]
    return render_template("migration/records.html", kind=kind, records=items)


@bp.route("/documents", methods=["GET", "POST"])
@tenant_view
def documents():
    tenant = g.migration_db
    if request.method == "POST":
        filename, contents = storage.receive(request.files.get("file"))
        form = request.form.to_dict()
        link = form.pop("link", "")
        if link:
            form["linked_type"], separator, form["linked_id"] = link.partition(":")
            if not separator:
                raise MigrationError("Invalid related record.")
        key = None
        try:
            version, key = upload_document(tenant, g.migration_org, current_user.id, filename, contents, form)
            tenant.commit()
        except Exception:
            if key:
                storage.resolve(g.migration_org, key).unlink(missing_ok=True)
            raise
        flash("Original retained. Review and approve the pending version before it becomes current.", "success")
        return redirect(url_for("migration.document_detail", document_id=version.document_id))
    docs = tenant.scalars(select(Document).order_by(Document.created_at.desc()).limit(200)).all()
    targets = []
    for kind, model in MODELS.items():
        query = select(model).limit(200)
        if kind in {"incident", "complaint"}:
            query = query.where(model.case_type == kind)
        targets.extend({"kind": kind, "id": x.id, "label": label(x)} for x in tenant.scalars(query))
    requirements = tenant.scalars(select(OrganisationRequirement)).all()
    return render_template("migration/documents.html", documents=docs, targets=targets, requirements=requirements)


@bp.get("/documents/<document_id>")
@tenant_view
def document_detail(document_id):
    document = g.migration_db.get(Document, document_id)
    if not document:
        abort(404)
    versions = []
    hash_matches = {}
    for version in sorted(document.versions, key=lambda x: -x.version_no):
        metadata = g.migration_db.scalar(select(MigrationAttachment).filter_by(document_version_id=version.id))
        versions.append((version, metadata))
        if metadata:
            hash_matches[version.id] = g.migration_db.scalars(select(MigrationAttachment.document_version_id).where(
                MigrationAttachment.sha256 == metadata.sha256,
                MigrationAttachment.document_version_id != version.id)).all()
    return render_template("migration/document.html", document=document, versions=versions, hash_matches=hash_matches)


@bp.post("/documents/versions/<version_id>/review")
@tenant_view
def version_review(version_id):
    if request.form.get("signoff") != "yes":
        raise MigrationError("Confirm you reviewed this original and its metadata.")
    review_document(g.migration_db, g.migration_org, version_id, current_user.id,
                    request.form.get("decision"), request.form.get("notes", ""))
    version = g.migration_db.get(DocumentVersion, version_id)
    return redirect(url_for("migration.document_detail", document_id=version.document_id))


@bp.get("/documents/versions/<version_id>/download")
@tenant_view
def version_download(version_id):
    version = g.migration_db.get(DocumentVersion, version_id)
    metadata = g.migration_db.scalar(select(MigrationAttachment).filter_by(document_version_id=version_id))
    if not version or not metadata:
        abort(404)
    return send_file(storage.verified_bytes(g.migration_org, version.file_path, metadata.sha256),
                     as_attachment=True, download_name=metadata.original_filename, mimetype="application/octet-stream")
