from app.extensions import db
from app.models.base import TimestampMixin, uuid_str


class Staff(TimestampMixin, db.Model):
    __tablename__ = "staff"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)

    # Optional link to a login account.
    # A staff record does not necessarily need a system login.
    user_id = db.Column(db.String(36), nullable=True)

    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)

    # Contact details that the worker may update themselves.
    contact_email = db.Column(db.String(255))
    phone_number = db.Column(db.String(50))

    employment_type = db.Column(db.String(80))
    position_title = db.Column(db.String(120))

    # Used to identify the worker's manager for notifications.
    line_manager_staff_id = db.Column(
        db.String(36),
        db.ForeignKey("tenant.staff.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

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

    # Location of the uploaded certificate/document.
    storage_key = db.Column(db.String(500))

    # Approval workflow.
    # pending -> approved / rejected
    review_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
    )

    submitted_by_user_id = db.Column(
        db.String(36),
        nullable=True,
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

    status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
    )

    storage_key = db.Column(db.String(500))

    verified_by_user_id = db.Column(db.String(36))
    verified_at = db.Column(db.DateTime(timezone=True))