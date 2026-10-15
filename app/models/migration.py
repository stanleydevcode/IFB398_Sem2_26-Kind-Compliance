"""Migration provenance lives in the same translated schema as its destination."""
from app.extensions import db
from app.models.base import TimestampMixin, uuid_str


class MigrationJob(TimestampMixin, db.Model):
    __tablename__ = "migration_jobs"
    __table_args__ = {"schema": "tenant"}
    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    record_type = db.Column(db.String(30), nullable=False)
    source_system = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    source_key = db.Column(db.String(500), nullable=False)
    source_sha256 = db.Column(db.String(64), nullable=False)
    uploaded_by = db.Column(db.String(36), db.ForeignKey("public.users.id"), nullable=False)
    headers = db.Column(db.JSON, nullable=False)
    mapping = db.Column(db.JSON, nullable=False, default=dict)
    date_format = db.Column(db.String(20), nullable=False, default="iso")
    status = db.Column(db.String(30), nullable=False, default="mapping")
    rows = db.relationship("MigrationRow", back_populates="job", order_by="MigrationRow.row_number")


class MigrationRow(TimestampMixin, db.Model):
    __tablename__ = "migration_rows"
    __table_args__ = (
        db.UniqueConstraint("job_id", "row_number", name="uq_migration_row_number"),
        {"schema": "tenant"},
    )
    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    job_id = db.Column(db.String(36), db.ForeignKey("tenant.migration_jobs.id"), nullable=False, index=True)
    row_number = db.Column(db.Integer, nullable=False)
    raw_data = db.Column(db.JSON, nullable=False)
    data = db.Column(db.JSON, nullable=False, default=dict)
    errors = db.Column(db.JSON, nullable=False, default=list)
    warnings = db.Column(db.JSON, nullable=False, default=list)
    candidates = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.String(30), nullable=False, default="unmapped")
    decision = db.Column(db.String(20), nullable=False, default="create")
    target_id = db.Column(db.String(36))
    target_snapshot = db.Column(db.String(64))
    decision_reason = db.Column(db.Text)
    approved_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    approved_at = db.Column(db.DateTime(timezone=True))
    destination_id = db.Column(db.String(36))
    job = db.relationship("MigrationJob", back_populates="rows")


class SourceIdentity(TimestampMixin, db.Model):
    __tablename__ = "migration_source_identities"
    __table_args__ = (
        db.UniqueConstraint("source_system", "entity_type", "source_reference", name="uq_migration_source"),
        {"schema": "tenant"},
    )
    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    source_system = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(30), nullable=False)
    source_reference = db.Column(db.String(150), nullable=False)
    destination_id = db.Column(db.String(36), nullable=False, index=True)


class MigrationAttachment(TimestampMixin, db.Model):
    """Sidecar metadata avoids altering the team's existing document tables."""
    __tablename__ = "migration_attachments"
    __table_args__ = {"schema": "tenant"}
    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    document_version_id = db.Column(db.String(36), db.ForeignKey("tenant.document_versions.id"), nullable=False, unique=True)
    original_filename = db.Column(db.String(255), nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    byte_size = db.Column(db.Integer, nullable=False)
    linked_type = db.Column(db.String(30))
    linked_id = db.Column(db.String(36))
    legacy_reference = db.Column(db.String(150))
    organisation_requirement_id = db.Column(db.String(36), db.ForeignKey("tenant.organisation_requirements.id"))


class MigrationChange(TimestampMixin, db.Model):
    """Restricted before/after values for explicitly reviewed updates."""
    __tablename__ = "migration_changes"
    __table_args__ = {"schema": "tenant"}
    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    row_id = db.Column(db.String(36), db.ForeignKey("tenant.migration_rows.id"), nullable=False)
    before = db.Column(db.JSON, nullable=False)
    after = db.Column(db.JSON, nullable=False)
