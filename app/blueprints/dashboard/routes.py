from datetime import date, timedelta

from flask import Blueprint, g, redirect, render_template, url_for
from sqlalchemy import select, func

from app.models import Staff, StaffCredential, Participant, Document, DocumentVersion, Case, Risk
from app.services import record_pages as pages

bp = Blueprint("dashboard", __name__)
pages.install_guards(bp)


@bp.get("/")
@pages.page
def index():
    if g.records_member.role not in pages.MANAGERS:
        return redirect(url_for("my_compliance.index"))
    tenant = g.records_db
    today = date.today()
    counts = {name:tenant.scalar(select(func.count()).select_from(model)) for name,model in
              [("workers",Staff),("participants",Participant)]}
    counts["documents"] = tenant.scalar(select(func.count()).select_from(Document).join(DocumentVersion,
        Document.current_version_id == DocumentVersion.id).where(DocumentVersion.approval_status == "approved"))
    counts["incidents"] = tenant.scalar(select(func.count()).select_from(Case).where(Case.case_type == "incident"))
    counts["credentials_pending"] = tenant.scalar(select(func.count()).select_from(StaffCredential).where(StaffCredential.status == "pending"))
    counts["versions_pending"] = tenant.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.approval_status == "pending"))
    expiring = tenant.scalars(select(StaffCredential).where(StaffCredential.expiry_date <= today+timedelta(days=30))
                              .order_by(StaffCredential.expiry_date).limit(10)).all()
    risks = tenant.scalars(select(Risk).where(Risk.status != "closed").order_by(Risk.review_date.asc().nulls_last(),Risk.title).limit(10)).all()
    return render_template("dashboard/index.html",counts=counts,expiring=expiring,risks=risks)
