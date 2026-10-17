from datetime import date, timedelta

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import Staff, StaffCredential, Membership, User, Document
from app.models.base import utcnow
from app.services import record_pages as pages
from app.services.permissions import can
from app.services.migration.engine import audit
from app.services.migration.reader import MigrationError
from app.services.migration import storage
from app.models.migration import MigrationAttachment

bp = Blueprint("staff", __name__, url_prefix="/staff")
pages.install_guards(bp)


@bp.get("/")
@pages.page
def index():
    pages.manager()
    tenant = g.records_db
    query = select(Staff).options(selectinload(Staff.credentials).selectinload(StaffCredential.credential_type))
    search = request.args.get("q", "").strip()[:100]
    if search:
        query = query.where((Staff.first_name + " " + Staff.last_name + " " + func.coalesce(Staff.email, "")).icontains(search, autoescape=True))
    active = request.args.get("active", "")
    tab = request.args.get("tab", "register")
    if tab not in {"register", "verify", "logins"}:
        abort(400)
    if tab == "logins" and not can(g.records_member.role, "manage_users"):
        abort(403)
    if active in {"yes", "no"}:
        query = query.where(Staff.is_active.is_(active == "yes"))
    workers = []
    pending = []
    if tab == "verify":
        pending, number, more = pages.paginate(tenant, select(StaffCredential).options(
            selectinload(StaffCredential.staff), selectinload(StaffCredential.credential_type)).where(
            StaffCredential.status == "pending").order_by(StaffCredential.created_at, StaffCredential.id))
    else:
        query = query.options(selectinload(Staff.user))
        workers, number, more = pages.paginate(tenant, query.order_by(Staff.last_name, Staff.first_name, Staff.id))
    today = date.today()
    counts = dict(
        active=tenant.scalar(select(func.count()).select_from(Staff).where(Staff.is_active.is_(True))),
        pending=tenant.scalar(select(func.count()).select_from(StaffCredential).where(StaffCredential.status == "pending")),
        expired=tenant.scalar(select(func.count()).select_from(StaffCredential).where(StaffCredential.expiry_date < today)),
        soon=tenant.scalar(select(func.count()).select_from(StaffCredential).where(StaffCredential.expiry_date.between(today, today+timedelta(days=30)))),
    )
    return render_template("staff/index.html", workers=workers, pending=pending, tab=tab,
                           counts=counts, page=number, more=more, search=search, active=active)


@bp.get("/<staff_id>")
@pages.page
def detail(staff_id):
    pages.manager()
    worker = pages.record(Staff, staff_id)
    return render_template("staff/detail.html", worker=worker,
        evidence=pages.linked_evidence(g.records_db, "staff", worker.id),
        sources=pages.provenance(g.records_db, "staff", worker.id))


@bp.route("/<staff_id>/edit", methods=["GET", "POST"])
@pages.page
def edit(staff_id):
    pages.manager()
    tenant = g.records_db
    worker = pages.record(Staff, staff_id)
    if request.method == "POST":
        reason = pages.checked_revision(worker)
        fields = ["first_name","last_name","email","phone","job_title","employment_type","start_date","is_active"]
        changed = pages.save_profile(tenant, worker, "staff", fields)
        if g.records_member.role == "organisation_admin":
            user_id = request.form.get("user_id") or None
            if user_id != worker.user_id:
                if user_id:
                    member = tenant.scalar(select(Membership).where(Membership.organisation_id == g.records_org,
                        Membership.user_id == user_id, Membership.is_active.is_(True)))
                    user = tenant.get(User, user_id)
                    linked = tenant.scalar(select(Staff).where(Staff.user_id == user_id, Staff.id != worker.id))
                    if not member or not user or not user.is_active or linked:
                        raise MigrationError("Select an active, unlinked login belonging to this organisation.")
                worker.user_id = user_id
                changed.append("user_id")
        elif "user_id" in request.form and (request.form.get("user_id") or None) != worker.user_id:
            abort(403)
        audit(tenant, current_user.id, "staff.updated", "staff", worker.id, {"fields":changed,"reason":reason})
        flash("Worker details saved. Login permissions were not changed.", "success")
        return redirect(url_for("staff.detail", staff_id=worker.id))
    logins = tenant.execute(select(User, Membership).join(Membership, User.id == Membership.user_id).where(
        Membership.organisation_id == g.records_org, Membership.is_active.is_(True), User.is_active.is_(True))).all()
    return render_template("staff/edit.html", worker=worker, logins=logins, linked_login_missing=bool(worker.user_id and worker.user_id not in {user.id for user,member in logins}))


@bp.post("/<staff_id>/credentials/<credential_id>/verify")
@pages.page
def verify(staff_id, credential_id):
    pages.manager()
    if not can(g.records_member.role, "approve_credential_renewal"):
        abort(403)
    tenant = g.records_db
    worker = pages.record(Staff, staff_id)
    credential = pages.record(StaffCredential, credential_id)
    if credential.staff_id != worker.id:
        abort(404)
    reason = pages.checked_revision(credential)
    document = tenant.get(Document, credential.document_id) if credential.document_id else None
    version = document.current_version if document else None
    if not version or version.approval_status != "approved" or request.form.get("version_id") != version.id:
        raise MigrationError("Review the current accepted evidence before verifying this credential.")
    metadata = tenant.scalar(select(MigrationAttachment).filter_by(document_version_id=version.id))
    if not metadata or metadata.linked_type != "credential" or metadata.linked_id != credential.id:
        raise MigrationError("The accepted original must be explicitly linked to this credential.")
    if credential.credential_type.has_expiry and not version.expiry_date:
        raise MigrationError("The accepted evidence needs an expiry date before verification.")
    if request.form.get("signoff") != "yes":
        raise MigrationError("Confirm you verified the original, identity, credential type and dates.")
    storage.verified_bytes(g.records_org, version.file_path, metadata.sha256)
    old_dates = {"issue_date":str(credential.issue_date or ""), "expiry_date":str(credential.expiry_date or "")}
    credential.issue_date, credential.expiry_date = version.issue_date, version.expiry_date
    credential.status, credential.verified_by, credential.verified_at = "verified", current_user.id, utcnow()
    credential.approved_by_user_id, credential.approved_at = current_user.id, utcnow()
    credential.review_notes = reason
    audit(tenant, current_user.id, "credential.verified", "credential", credential.id,
          {"document_version_id":version.id,"old_dates":old_dates,
           "new_dates":{"issue_date":str(version.issue_date or ""),"expiry_date":str(version.expiry_date or "")}})
    flash("Credential verification recorded. Its expiry condition remains separate.", "success")
    return redirect(url_for("staff.detail", staff_id=worker.id))
