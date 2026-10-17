from app.extensions import db
from app.models.base import TimestampMixin, uuid_str, utcnow


class OrganisationRegistrationGroup(TimestampMixin, db.Model):
    __tablename__ = "organisation_registration_groups"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    registration_group_code = db.Column(
        db.String(20), db.ForeignKey("public.registration_groups.code"), nullable=False,
    )
    registered_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    status = db.Column(db.String(30), nullable=False, default="selected")

    registration_group = db.relationship("RegistrationGroup")


class OrganisationRequirement(TimestampMixin, db.Model):
    __tablename__ = "organisation_requirements"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    requirement_id = db.Column(
        db.Integer, db.ForeignKey("public.compliance_requirements.id"), nullable=False,
    )
    status = db.Column(db.String(30), nullable=False, default="missing")
    due_date = db.Column(db.Date)

    requirement = db.relationship("ComplianceRequirement")
    evidence_links = db.relationship("EvidenceLink", back_populates="organisation_requirement")
