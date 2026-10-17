from flask import Blueprint, abort, g, render_template
from sqlalchemy import select

from app.models import Participant, StaffCredential, DocumentVersion
from app.models.migration import MigrationAttachment
from app.services import record_pages as pages

bp = Blueprint("my_compliance", __name__, url_prefix="/my-compliance")
pages.install_guards(bp)


@bp.get("/")
@pages.page
def index():
    worker = pages.own_staff(g.records_db)
    participants = g.records_db.scalars(select(Participant).where(Participant.key_worker_staff_id == worker.id)
                                        .order_by(Participant.last_name)).all() if worker else []
    evidence = g.records_db.execute(select(MigrationAttachment,DocumentVersion).join(DocumentVersion,
        MigrationAttachment.document_version_id == DocumentVersion.id).join(StaffCredential,
        MigrationAttachment.linked_id == StaffCredential.id).where(MigrationAttachment.linked_type == "credential",
        StaffCredential.staff_id == worker.id,DocumentVersion.approval_status == "approved")).all() if worker else []
    return render_template("my_compliance/index.html",worker=worker,participants=participants,evidence=evidence)


@bp.get("/evidence/<version_id>")
@pages.page
def download(version_id):
    tenant = g.records_db
    worker = pages.own_staff(tenant)
    if not worker:
        abort(404)
    found = tenant.scalar(select(DocumentVersion).join(MigrationAttachment,
        MigrationAttachment.document_version_id == DocumentVersion.id).join(StaffCredential,
        StaffCredential.id == MigrationAttachment.linked_id).where(DocumentVersion.id == version_id,
        DocumentVersion.approval_status == "approved",MigrationAttachment.linked_type == "credential",
        StaffCredential.staff_id == worker.id))
    if not found:
        abort(404)
    return pages.download_version(tenant,version_id)
