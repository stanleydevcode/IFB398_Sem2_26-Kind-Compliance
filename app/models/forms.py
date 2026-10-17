from app.extensions import db
from app.models.base import TimestampMixin, uuid_str, utcnow


class FormTemplate(TimestampMixin, db.Model):
    __tablename__ = "form_templates"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    name = db.Column(db.String(250), nullable=False)
    form_type = db.Column(db.String(80), nullable=False)
    schema_definition = db.Column(db.JSON, nullable=False, default=dict)

    submissions = db.relationship("FormSubmission", back_populates="template")


class FormSubmission(TimestampMixin, db.Model):
    __tablename__ = "form_submissions"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    form_template_id = db.Column(
        db.String(36), db.ForeignKey("tenant.form_templates.id"), nullable=False, index=True,
    )
    submitted_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    data = db.Column(db.JSON, nullable=False, default=dict)
    related_entity_type = db.Column(db.String(80))
    related_entity_id = db.Column(db.String(36))
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    template = db.relationship("FormTemplate", back_populates="submissions")
    submitter = db.relationship("User")
    evidence_links = db.relationship("EvidenceLink", back_populates="form_submission")
