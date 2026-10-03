from app.extensions import db
from app.models.base import TimestampMixin

class CredentialType(TimestampMixin, db.Model):
    __tablename__ = "credential_types"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
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
    audit_pathway = db.Column(db.String(30), nullable=False)  # verification/certification

class ComplianceRequirement(TimestampMixin, db.Model):
    __tablename__ = "compliance_requirements"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    requirement_code = db.Column(db.String(100), unique=True, nullable=False)
    compliance_area_code = db.Column(
        db.String(50),
        db.ForeignKey("public.compliance_areas.code"),
        nullable=False,
    )
    registration_group_code = db.Column(
        db.String(20),
        db.ForeignKey("public.registration_groups.code"),
        nullable=True,
    )
    document_type_code = db.Column(
        db.String(50),
        db.ForeignKey("public.document_types.code"),
        nullable=True,
    )
    name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    is_conditional = db.Column(db.Boolean, nullable=False, default=False)
