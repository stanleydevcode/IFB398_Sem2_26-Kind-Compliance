from app.extensions import db
from app.models.base import TimestampMixin, uuid_str

class OrganisationRegistrationGroup(TimestampMixin, db.Model):
    __tablename__ = "organisation_registration_groups"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    registration_group_code = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="selected")

class OrganisationRequirement(TimestampMixin, db.Model):
    __tablename__ = "organisation_requirements"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    requirement_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="missing")
    due_date = db.Column(db.Date)
