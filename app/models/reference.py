from sqlalchemy.orm import synonym

from app.extensions import db
from app.models.base import TimestampMixin


class CredentialType(TimestampMixin, db.Model):
    __tablename__ = "credential_types"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    has_expiry = db.Column(db.Boolean, nullable=False, default=True)
    default_validity_days = db.Column(db.Integer)


class DocumentType(TimestampMixin, db.Model):
    __tablename__ = "document_types"
    __table_args__ = {"schema": "public"}

    code = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)


class ComplianceArea(TimestampMixin, db.Model):
    __tablename__ = "compliance_areas"
    __table_args__ = {"schema": "public"}

    code = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)


class RegistrationGroup(TimestampMixin, db.Model):
    __tablename__ = "registration_groups"
    __table_args__ = {"schema": "public"}

    code = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    audit_pathway = db.Column(db.String(30), nullable=False)

    module_links = db.relationship(
        "RegistrationGroupModule", back_populates="registration_group",
        cascade="all, delete", passive_deletes=True,
    )
    practice_modules = db.relationship(
        "PracticeModule", secondary="public.registration_group_modules", viewonly=True,
        back_populates="registration_groups",
    )


class PracticeModule(TimestampMixin, db.Model):
    __tablename__ = "practice_modules"
    __table_args__ = {"schema": "public"}

    code = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(250), nullable=False)

    registration_group_links = db.relationship(
        "RegistrationGroupModule", back_populates="practice_module",
        cascade="all, delete", passive_deletes=True,
    )
    registration_groups = db.relationship(
        "RegistrationGroup", secondary="public.registration_group_modules", viewonly=True,
        back_populates="practice_modules",
    )


class RegistrationGroupModule(db.Model):
    __tablename__ = "registration_group_modules"
    __table_args__ = {"schema": "public"}

    registration_group_code = db.Column(
        db.String(20), db.ForeignKey("public.registration_groups.code", ondelete="CASCADE"),
        primary_key=True,
    )
    practice_module_code = db.Column(
        db.String(50), db.ForeignKey("public.practice_modules.code", ondelete="CASCADE"),
        primary_key=True,
    )

    registration_group = db.relationship("RegistrationGroup", back_populates="module_links")
    practice_module = db.relationship("PracticeModule", back_populates="registration_group_links")


class ComplianceRequirement(TimestampMixin, db.Model):
    __tablename__ = "compliance_requirements"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    requirement_code = db.Column(db.String(100), unique=True)
    compliance_area_code = db.Column(
        db.String(50), db.ForeignKey("public.compliance_areas.code"), nullable=False,
    )
    registration_group_code = db.Column(db.String(20), db.ForeignKey("public.registration_groups.code"))
    practice_module_code = db.Column(db.String(50), db.ForeignKey("public.practice_modules.code"))
    document_type_code = db.Column(db.String(50), db.ForeignKey("public.document_types.code"))
    name = db.Column(db.String(250), nullable=False)
    source_type = db.Column(db.String(80))
    conditional = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)

    is_conditional = synonym("conditional")
    description = synonym("notes")
    compliance_area = db.relationship("ComplianceArea")
    registration_group = db.relationship("RegistrationGroup")
    practice_module = db.relationship("PracticeModule")
    document_type = db.relationship("DocumentType")
