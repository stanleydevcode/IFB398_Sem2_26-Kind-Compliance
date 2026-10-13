from sqlalchemy.orm import synonym

from app.extensions import db
from app.models.base import TimestampMixin, uuid_str, utcnow


class Document(TimestampMixin, db.Model):
    __tablename__ = "documents"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    document_type_code = db.Column(db.String(50), db.ForeignKey("public.document_types.code"))
    compliance_area_code = db.Column(db.String(50), db.ForeignKey("public.compliance_areas.code"))
    current_version_id = db.Column(
        db.String(36),
        db.ForeignKey("tenant.document_versions.id", name="fk_document_current_version",
                      use_alter=True, ondelete="SET NULL"),
    )
    title = db.Column(db.String(250), nullable=False)
    category = db.Column(db.String(100))
    document_kind = db.Column(db.String(50))
    status = db.Column(db.String(30), nullable=False, default="draft")
    expiry_date = db.Column(db.Date)
    review_date = db.Column(db.Date)
    # Retained for callers that display the current version number.
    current_version_number = db.Column(db.Integer)

    document_type = db.relationship("DocumentType")
    compliance_area = db.relationship("ComplianceArea")
    versions = db.relationship(
        "DocumentVersion", foreign_keys="DocumentVersion.document_id", back_populates="document",
        cascade="all, delete", passive_deletes=True,
    )
    current_version = db.relationship(
        "DocumentVersion", foreign_keys=[current_version_id], post_update=True,
    )
    evidence_links = db.relationship(
        "EvidenceLink", back_populates="document", cascade="all, delete", passive_deletes=True,
    )
    acknowledgements = db.relationship("DocumentAcknowledgement", back_populates="document")


class DocumentVersion(TimestampMixin, db.Model):
    __tablename__ = "document_versions"
    __table_args__ = (
        db.UniqueConstraint("document_id", "version_no", name="uq_doc_version"),
        {"schema": "tenant"},
    )

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    document_id = db.Column(
        db.String(36), db.ForeignKey("tenant.documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    version_no = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    review_date = db.Column(db.Date)
    uploaded_by = db.Column(db.String(36), db.ForeignKey("public.users.id"), nullable=False)
    approved_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    approval_status = db.Column(db.String(30), nullable=False, default="pending")
    approval_notes = db.Column(db.Text)
    approval_at = db.Column(db.DateTime(timezone=True))
    uploaded_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    version_number = synonym("version_no")
    storage_key = synonym("file_path")
    uploaded_by_user_id = synonym("uploaded_by")
    approved_by_user_id = synonym("approved_by")
    review_status = synonym("approval_status")
    review_notes = synonym("approval_notes")
    approved_at = synonym("approval_at")
    document = db.relationship("Document", foreign_keys=[document_id], back_populates="versions")
    uploader = db.relationship("User", foreign_keys=[uploaded_by])
    approver = db.relationship("User", foreign_keys=[approved_by])


class EvidenceLink(TimestampMixin, db.Model):
    __tablename__ = "evidence_links"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    organisation_requirement_id = db.Column(
        db.String(36), db.ForeignKey("tenant.organisation_requirements.id"),
        nullable=False, index=True,
    )
    reviewed_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    form_submission_id = db.Column(db.String(36), db.ForeignKey("tenant.form_submissions.id"))
    document_id = db.Column(
        db.String(36), db.ForeignKey("tenant.documents.id", ondelete="CASCADE"),
    )
    status = db.Column(db.String(30), nullable=False, default="linked")
    reviewed_at = db.Column(db.DateTime(timezone=True))

    reviewed_by_user_id = synonym("reviewed_by")
    organisation_requirement = db.relationship("OrganisationRequirement", back_populates="evidence_links")
    form_submission = db.relationship("FormSubmission", back_populates="evidence_links")
    document = db.relationship("Document", back_populates="evidence_links")
    reviewer = db.relationship("User")


class DocumentAcknowledgement(TimestampMixin, db.Model):
    __tablename__ = "document_acknowledgements"
    __table_args__ = (
        db.UniqueConstraint("document_id", "staff_id", name="uq_doc_staff_ack"),
        {"schema": "tenant"},
    )

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    document_id = db.Column(db.String(36), db.ForeignKey("tenant.documents.id"), nullable=False)
    staff_id = db.Column(db.String(36), db.ForeignKey("tenant.staff.id"), nullable=False)
    acknowledged_at = db.Column(db.DateTime(timezone=True))

    document = db.relationship("Document", back_populates="acknowledgements")
    staff = db.relationship("Staff")
