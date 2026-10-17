"""Original files and metadata; no OCR or automatic evidence verification."""
from datetime import date

from sqlalchemy import func, select

from app.models import Document, DocumentVersion, StaffCredential, EvidenceLink, OrganisationRequirement
from app.models.base import utcnow
from app.models.migration import MigrationAttachment
from app.services.migration import storage
from app.services.migration.engine import MODELS, audit
from app.services.migration.reader import MigrationError


def upload_document(session, organisation_id, actor, filename, contents, form, audit_prefix="migration"):
    storage.validate_document(filename, contents)
    title = form.get("title", "").strip()
    kind = form.get("document_kind", "policy")
    category = form.get("category", "").strip()
    legacy = form.get("legacy_reference", "").strip()
    if not title or len(title) > 250 or len(category) > 100 or len(legacy) > 150:
        raise MigrationError("Enter a title up to 250 characters; category up to 100 and legacy reference up to 150.")
    if kind not in {"policy", "procedure", "credential", "consent", "form", "register", "other"}:
        raise MigrationError("Invalid document kind.")
    dates = {}
    for key in ("issue_date", "expiry_date", "review_date"):
        try:
            dates[key] = date.fromisoformat(form[key]) if form.get(key) else None
        except ValueError as exc:
            raise MigrationError("Document dates must be YYYY-MM-DD.") from exc
    if dates["issue_date"] and dates["expiry_date"] and dates["expiry_date"] < dates["issue_date"]:
        raise MigrationError("Expiry cannot precede issue date.")
    document_id = form.get("document_id")
    document = session.scalar(select(Document).where(Document.id == document_id).with_for_update()) if document_id else None
    if document_id and not document:
        raise MigrationError("Document is unavailable in this organisation.")
    linked_type, linked_id = form.get("linked_type", ""), form.get("linked_id", "")
    if document:
        attached_credentials = session.scalars(select(StaffCredential).where(StaffCredential.document_id == document.id)).all()
        if attached_credentials and (linked_type != "credential" or any(c.id != linked_id for c in attached_credentials)):
            raise MigrationError("A replacement credential original must retain its existing credential link.")
    if linked_type or linked_id:
        if linked_type not in MODELS or not linked_id:
            raise MigrationError("Choose a valid related record.")
        target = session.get(MODELS[linked_type], linked_id)
        if target is None or (linked_type in {"incident", "complaint"} and target.case_type != linked_type):
            raise MigrationError("Related record is unavailable in this organisation.")
        if linked_type == "credential" and target.document_id and (not document or target.document_id != document.id):
            raise MigrationError("This credential already has a document. Upload a new version of that document.")
    requirement_id = form.get("requirement_id") or None
    if requirement_id and session.get(OrganisationRequirement, requirement_id) is None:
        raise MigrationError("Requirement is unavailable in this organisation.")
    if not document:
        document = Document(title=title, category=category or None, document_kind=kind, status="draft")
        session.add(document)
        session.flush()
    number = (session.scalar(select(func.max(DocumentVersion.version_no)).where(
        DocumentVersion.document_id == document.id)) or 0) + 1
    key, digest = storage.save(organisation_id, contents)
    try:
        version = DocumentVersion(document_id=document.id, version_no=number, file_path=key,
                                  uploaded_by=actor, approval_status="pending", **dates)
        session.add(version)
        session.flush()
        metadata = MigrationAttachment(document_version_id=version.id, original_filename=filename,
            sha256=digest, byte_size=len(contents), linked_type=linked_type or None,
            linked_id=linked_id or None, legacy_reference=legacy or None,
            organisation_requirement_id=requirement_id)
        session.add(metadata)
        audit(session, actor, audit_prefix + ".document_uploaded", "document_version", version.id,
              {"document_id": document.id, "version": number, "sha256": digest})
        session.flush()
        return version, key
    except Exception:
        storage.resolve(organisation_id, key).unlink(missing_ok=True)
        raise


def review_document(session, organisation_id, version_id, actor, decision, notes, audit_prefix="migration"):
    version = session.scalar(select(DocumentVersion).where(DocumentVersion.id == version_id).with_for_update())
    if not version or version.approval_status != "pending":
        raise MigrationError("Only a pending version can be reviewed.")
    if decision not in {"approved", "returned"} or not notes.strip() or len(notes) > 2000:
        raise MigrationError("Choose approve/return and give review notes up to 2,000 characters.")
    metadata = session.scalar(select(MigrationAttachment).filter_by(document_version_id=version.id))
    if not metadata:
        raise MigrationError("This version was not uploaded through migration.")
    document = session.get(Document, version.document_id)
    if decision == "approved":
        storage.verified_bytes(organisation_id, version.file_path, metadata.sha256)
        attached_credentials = session.scalars(select(StaffCredential).where(StaffCredential.document_id == document.id)).all()
        if attached_credentials and (metadata.linked_type != "credential" or any(c.id != metadata.linked_id for c in attached_credentials)):
            raise MigrationError("This pending version does not retain the existing credential link. Return it and upload the correctly linked original.")
        if document.current_version_number and document.current_version_number >= version.version_no:
            raise MigrationError("A newer version is already current. Return this older pending version instead.")
        document.current_version_id = version.id
        document.current_version_number = version.version_no
        document.expiry_date, document.review_date = version.expiry_date, version.review_date
        document.status = "approved"
        if metadata.linked_type == "credential":
            credential = session.get(StaffCredential, metadata.linked_id)
            if credential is None or (credential.document_id and credential.document_id != document.id):
                raise MigrationError("Credential/document link changed. Return the version and upload with the correct link.")
            credential.document_id = document.id
            # A newly accepted original cannot inherit verification of an earlier version.
            credential.status = "pending"
            credential.verified_by = None
            credential.verified_at = None
            credential.approved_by_user_id = None
            credential.approved_at = None
            # Evidence acceptance is a separate review from professional verification.
        if metadata.organisation_requirement_id:
            exists = session.scalar(select(EvidenceLink).filter_by(
                document_id=document.id, organisation_requirement_id=metadata.organisation_requirement_id))
            if not exists:
                session.add(EvidenceLink(document_id=document.id,
                    organisation_requirement_id=metadata.organisation_requirement_id, status="linked"))
    version.approval_status, version.approval_notes = decision, notes.strip()
    version.approved_by, version.approval_at = actor, utcnow()
    audit(session, actor, audit_prefix + ".document_" + decision, "document_version", version.id,
          {"document_id": document.id, "version": version.version_no})


def date_condition(version, today=None):
    today = today or date.today()
    if version.expiry_date and version.expiry_date < today:
        return "Expired"
    if version.review_date and version.review_date < today:
        return "Review overdue"
    due = [d for d in (version.expiry_date, version.review_date) if d]
    if due and (min(due) - today).days <= 30:
        return "Due within 30 days"
    return "Current dates" if due else "No tracking date"
