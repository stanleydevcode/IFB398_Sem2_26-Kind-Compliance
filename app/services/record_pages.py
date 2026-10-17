"""Tenant-scoped projections and guards for the connected domain pages."""
import hmac
import secrets
from datetime import date
from functools import wraps

from flask import abort, current_app, g, render_template, request, session
from flask_login import current_user
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError

from app import decorators
from app.constants import Roles
from app.models import (Staff, StaffCredential, Participant, Document, DocumentVersion,
                        ServiceAgreement)
from app.models.migration import MigrationAttachment, SourceIdentity
from app.services.migration.documents import date_condition
from app.services.migration.engine import audit, fingerprint, lock_imports, normalise
from app.services.migration.reader import MigrationError
from app.services.migration import storage
from app.services.tenant import tenant_session

MANAGERS = {Roles.ORGANISATION_ADMIN, Roles.COMPLIANCE_MANAGER}


def csrf_token():
    if "records_csrf" not in session:
        session["records_csrf"] = secrets.token_urlsafe(32)
    return session["records_csrf"]


def install_guards(bp):
    @bp.before_request
    def authorise():
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        member = decorators.current_membership()
        if not member or not member.organisation.is_active:
            abort(403)
        g.records_member = member
        g.records_org = member.organisation_id
        request.max_content_length = 11 * 1024 * 1024
        if request.method == "POST" and not hmac.compare_digest(request.form.get("csrf_token", ""), csrf_token()):
            abort(400, description="Your form expired. Reload the page and try again.")

    @bp.context_processor
    def context():
        return dict(records_csrf=csrf_token, date_condition=date_condition, credential_dates=credential_dates,
                    fingerprint=fingerprint, credential_tone=credential_tone)

    @bp.after_request
    def protect(response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @bp.errorhandler(MigrationError)
    def invalid(error):
        return render_template("shared/record_error.html", message=str(error)), 400

    @bp.errorhandler(SQLAlchemyError)
    def unavailable(error):
        current_app.logger.error("Record operation failed (%s)", type(error).__name__)
        return render_template("shared/record_error.html", message="The database operation could not complete and was rolled back. Check the connection and migration-init setup, then reload and retry."), 409


def page(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        with tenant_session(g.records_org) as tenant:
            g.records_db = tenant
            if request.method == "POST":
                lock_imports(tenant, g.records_org)
            return view(*args, **kwargs)
    return wrapped


def manager():
    if g.records_member.role not in MANAGERS:
        abort(403)


def record(model, identifier):
    value = g.records_db.get(model, identifier)
    if value is None:
        abort(404)
    return value


def own_staff(tenant):
    return tenant.scalar(select(Staff).where(Staff.user_id == current_user.id, Staff.is_active.is_(True)))


def allowed_participant(tenant, participant):
    if g.records_member.role in MANAGERS:
        return True
    staff = own_staff(tenant)
    return bool(staff and participant.key_worker_staff_id == staff.id)


def participant_or_404(identifier):
    participant = record(Participant, identifier)
    if not allowed_participant(g.records_db, participant):
        abort(404)
    return participant


def credential_dates(credential, today=None):
    today = today or date.today()
    if not credential.expiry_date:
        return "Expiry missing" if credential.credential_type.has_expiry else "No expiry required"
    if credential.expiry_date < today:
        return "Expired"
    if (credential.expiry_date - today).days <= 30:
        return "Due within 30 days"
    return "Current dates"


def credential_tone(credential):
    """Date/review presentation only; this is not a compliance decision."""
    condition = credential_dates(credential)
    if condition == "Expired":
        return "bad"
    if condition in {"Expiry missing", "Due within 30 days"} or credential.status != "verified":
        return "warn"
    return "neutral"


def page_number():
    try:
        return max(1, int(request.args.get("page", "1")))
    except ValueError:
        abort(400)


def paginate(tenant, query, page_size=50):
    number = page_number()
    items = tenant.scalars(query.offset((number-1)*page_size).limit(page_size+1)).all()
    return items[:page_size], number, len(items) > page_size


def provenance(tenant, kind, identifier):
    return tenant.scalars(select(SourceIdentity).where(SourceIdentity.entity_type == kind,
        SourceIdentity.destination_id == identifier).order_by(SourceIdentity.source_system)).all()


def linked_evidence(tenant, kind, identifier):
    clauses = [((MigrationAttachment.linked_type == kind) & (MigrationAttachment.linked_id == identifier))]
    doc_ids = []
    if kind == "staff":
        credentials = tenant.scalars(select(StaffCredential).where(StaffCredential.staff_id == identifier)).all()
        ids = [c.id for c in credentials]
        if ids:
            clauses.append((MigrationAttachment.linked_type == "credential") & MigrationAttachment.linked_id.in_(ids))
        doc_ids.extend(c.document_id for c in credentials if c.document_id)
    if kind == "participant":
        doc_ids.extend(tenant.scalars(select(ServiceAgreement.document_id).where(ServiceAgreement.participant_id == identifier)))
    direct = tenant.execute(select(MigrationAttachment, DocumentVersion, Document).join(
        DocumentVersion, MigrationAttachment.document_version_id == DocumentVersion.id).join(
        Document, DocumentVersion.document_id == Document.id).where(or_(*clauses))).all()
    by_id = {v.id: dict(metadata=m, version=v, document=d) for m,v,d in direct}
    if doc_ids:
        for m,v,d in tenant.execute(select(MigrationAttachment, DocumentVersion, Document).join(
            DocumentVersion, MigrationAttachment.document_version_id == DocumentVersion.id).join(
            Document, DocumentVersion.document_id == Document.id).where(Document.id.in_(doc_ids))):
            by_id.setdefault(v.id, dict(metadata=m, version=v, document=d))
    result = list(by_id.values())
    if g.records_member.role not in MANAGERS:
        # Per-version link check: a document may have versions linked to different records.
        result = [x for x in result if x["version"].approval_status == "approved" and
                  x["metadata"].linked_type == "participant" and x["metadata"].linked_id == identifier]
    return sorted(result, key=lambda x:(x["document"].title, -x["version"].version_no))


def download_version(tenant, version_id):
    from flask import send_file
    version = record(DocumentVersion, version_id)
    meta = tenant.scalar(select(MigrationAttachment).filter_by(document_version_id=version.id))
    if not meta:
        raise MigrationError("This original was stored outside the protected upload service. Contact the document owner to make it available securely.")
    return send_file(storage.verified_bytes(g.records_org, version.file_path, meta.sha256),
                     as_attachment=True, download_name=meta.original_filename, mimetype="application/octet-stream")


def checked_revision(value):
    if request.form.get("revision") != fingerprint(value):
        raise MigrationError("This record changed in another window. Reload and review the latest values.")
    reason = request.form.get("reason", "").strip()
    if not reason or len(reason) > 1000:
        raise MigrationError("Give a change reason up to 1,000 characters.")
    return reason


def save_profile(tenant, value, kind, fields):
    """Normal edits share the importer's field validation, using ISO dates."""
    from types import SimpleNamespace
    supplied = {key: request.form.get(key, "") for key in fields}
    data, errors, _ = normalise(SimpleNamespace(record_type=kind, date_format="iso"), supplied)
    if errors:
        raise MigrationError(" ".join(errors))
    changed = []
    for key in fields:
        val = data.get(key) or None
        if key == "is_active":
            val = data.get(key) == "yes"
        elif val and key in {"start_date", "date_of_birth", "plan_start_date", "plan_end_date"}:
            val = date.fromisoformat(val)
        if getattr(value, key) != val:
            changed.append(key)
            setattr(value, key, val)
    return changed
