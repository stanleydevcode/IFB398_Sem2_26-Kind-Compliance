from app.extensions import db
from app.models.base import TimestampMixin, uuid_str

class Staff(TimestampMixin, db.Model):
    __tablename__ = "staff"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    user_id = db.Column(db.String(36), nullable=True)  # points to public.users logically
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    employment_type = db.Column(db.String(80))
    position_title = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, nullable=False, default=True)

class StaffCredential(TimestampMixin, db.Model):
    __tablename__ = "staff_credentials"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    staff_id = db.Column(
        db.String(36),
        db.ForeignKey("tenant.staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credential_type_id = db.Column(db.Integer, nullable=False)
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="pending")
    storage_key = db.Column(db.String(500))
    verified_by_user_id = db.Column(db.String(36))
    verified_at = db.Column(db.DateTime(timezone=True))
