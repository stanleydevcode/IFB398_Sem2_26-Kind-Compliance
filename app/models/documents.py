from app.extensions import db
from app.models.base import TimestampMixin, uuid_str


class Document(TimestampMixin, db.Model):
    __tablename__ = "documents"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    document_type_code = db.Column(
        db.String(50),
        nullable=True,
    )

    title = db.Column(
        db.String(250),
        nullable=False,
    )

    category = db.Column(
        db.String(100),
        nullable=True,
    )

    # Examples:
    # policy
    # procedure
    # form
    # register
    # certificate
    # other
    document_kind = db.Column(
        db.String(50),
        nullable=True,
    )

    # Overall document state.
    # draft / current / archived
    status = db.Column(
        db.String(30),
        nullable=False,
        default="draft",
    )

    # Points to the version that is currently approved/current.
    # This can be empty while a policy/procedure is waiting for approval.
    current_version_number = db.Column(
        db.Integer,
        nullable=True,
    )


class DocumentVersion(TimestampMixin, db.Model):
    __tablename__ = "document_versions"
    __table_args__ = (
        db.UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_doc_version",
        ),
        {"schema": "tenant"},
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    document_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "tenant.documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    version_number = db.Column(
        db.Integer,
        nullable=False,
    )

    storage_key = db.Column(
        db.String(500),
        nullable=False,
    )

    issue_date = db.Column(
        db.Date,
        nullable=True,
    )

    expiry_date = db.Column(
        db.Date,
        nullable=True,
    )

    review_date = db.Column(
        db.Date,
        nullable=True,
    )

    uploaded_by_user_id = db.Column(
        db.String(36),
        nullable=False,
    )

    # Approval workflow:
    #
    # pending
    # approved
    # rejected
    # not_required
    review_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
    )

    approved_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    approved_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    review_notes = db.Column(
        db.Text,
        nullable=True,
    )


class EvidenceLink(TimestampMixin, db.Model):
    __tablename__ = "evidence_links"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    requirement_id = db.Column(
        db.Integer,
        nullable=False,
    )

    document_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "tenant.documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="linked",
    )

    reviewed_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    reviewed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )


class DocumentAcknowledgement(TimestampMixin, db.Model):
    __tablename__ = "document_acknowledgements"
    __table_args__ = (
        db.UniqueConstraint(
            "document_id",
            "staff_id",
            name="uq_doc_staff_ack",
        ),
        {"schema": "tenant"},
    )

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    document_id = db.Column(
        db.String(36),
        nullable=False,
    )

    staff_id = db.Column(
        db.String(36),
        nullable=False,
    )

    acknowledged_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )