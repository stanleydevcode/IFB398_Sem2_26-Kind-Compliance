from sqlalchemy.orm import synonym

from app.extensions import db
from app.models.base import TimestampMixin, uuid_str


class Staff(TimestampMixin, db.Model):
    __tablename__ = "staff"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    # Some workers have no login account.
    user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"), unique=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    job_title = db.Column(db.String(120))
    start_date = db.Column(db.Date)
    employment_type = db.Column(db.String(80))
    line_manager_staff_id = db.Column(
        db.String(36), db.ForeignKey("tenant.staff.id", ondelete="SET NULL"), index=True,
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    contact_email = synonym("email")
    phone_number = synonym("phone")
    position_title = synonym("job_title")
    user = db.relationship("User")
    line_manager = db.relationship("Staff", remote_side=[id], foreign_keys=[line_manager_staff_id])
    credentials = db.relationship(
        "StaffCredential", back_populates="staff", cascade="all, delete", passive_deletes=True,
    )


class StaffCredential(TimestampMixin, db.Model):
    __tablename__ = "staff_credentials"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    staff_id = db.Column(
        db.String(36), db.ForeignKey("tenant.staff.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    credential_type_id = db.Column(db.Integer, db.ForeignKey("public.credential_types.id"), nullable=False)
    document_id = db.Column(db.String(36), db.ForeignKey("tenant.documents.id"))
    verified_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="pending")
    verified_at = db.Column(db.DateTime(timezone=True))
    storage_key = db.Column(db.String(500))
    submitted_by_user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    approved_by_user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    approved_at = db.Column(db.DateTime(timezone=True))
    review_notes = db.Column(db.Text)

    review_status = synonym("status")
    verified_by_user_id = synonym("verified_by")
    staff = db.relationship("Staff", back_populates="credentials")
    credential_type = db.relationship("CredentialType")
    document = db.relationship("Document")
    verifier = db.relationship("User", foreign_keys=[verified_by])
    submitter = db.relationship("User", foreign_keys=[submitted_by_user_id])
    approver = db.relationship("User", foreign_keys=[approved_by_user_id])
