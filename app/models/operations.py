from app.extensions import db
from app.models.base import TimestampMixin, uuid_str

class IncidentCase(TimestampMixin, db.Model):
    __tablename__ = "incident_cases"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    reference = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )

    participant_id = db.Column(
        db.String(36),
        nullable=True,
    )

    reported_by_staff_id = db.Column(
        db.String(36),
        nullable=True,
    )

    # incident / complaint
    category = db.Column(
        db.String(80),
        nullable=False,
    )

    # When and where the actual event happened.
    occurred_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    location = db.Column(
        db.String(250),
        nullable=True,
    )

    description = db.Column(
        db.Text,
        nullable=False,
    )

    immediate_response = db.Column(
        db.Text,
        nullable=True,
    )

    severity = db.Column(
        db.String(30),
        nullable=True,
    )

    # reported
    # under_review
    # investigation
    # action_required
    # resolved
    # closed
    status = db.Column(
        db.String(40),
        nullable=False,
        default="reported",
    )

    assigned_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    investigation_notes = db.Column(
        db.Text,
        nullable=True,
    )

    outcome = db.Column(
        db.Text,
        nullable=True,
    )

    # -----------------------------
    # Reportability decision
    # -----------------------------

    reportable = db.Column(
        db.Boolean,
        nullable=True,
    )

    reportability_reason = db.Column(
        db.Text,
        nullable=True,
    )

    reportability_decided_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    reportability_decided_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------
    # NDIS Commission reference
    # Administrator only
    # -----------------------------

    commission_reference = db.Column(
        db.String(100),
        nullable=True,
    )

    commission_reference_recorded_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    commission_reference_recorded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------
    # Case closure
    # Compliance Manager only
    # -----------------------------

    closed_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    closed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    closure_notes = db.Column(
        db.Text,
        nullable=True,
    )
    __tablename__ = "incident_cases"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    participant_id = db.Column(db.String(36))
    reported_by_staff_id = db.Column(db.String(36))
    category = db.Column(db.String(80), nullable=False)  # incident / complaint / etc.
    description = db.Column(db.Text, nullable=False)
    immediate_response = db.Column(db.Text)
    severity = db.Column(db.String(30))
    status = db.Column(db.String(40), nullable=False, default="reported")
    reportable = db.Column(db.Boolean)
    reportability_reason = db.Column(db.Text)
    commission_reference = db.Column(db.String(100))
    assigned_user_id = db.Column(db.String(36))

class Risk(TimestampMixin, db.Model):
    __tablename__ = "risks"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    title = db.Column(
        db.String(250),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    category = db.Column(
        db.String(100),
        nullable=True,
    )

    # Risk assessment
    likelihood = db.Column(
        db.String(30),
        nullable=True,
    )

    consequence = db.Column(
        db.String(30),
        nullable=True,
    )

    rating = db.Column(
        db.String(30),
        nullable=True,
    )

    # Existing controls already in place.
    existing_controls = db.Column(
        db.Text,
        nullable=True,
    )

    # Additional treatment / mitigation.
    treatment = db.Column(
        db.Text,
        nullable=True,
    )

    # Person responsible for reviewing the risk.
    owner_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    # The next required review date.
    review_date = db.Column(
        db.Date,
        nullable=True,
    )

    # Details of the most recent review.
    last_reviewed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    last_reviewed_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    review_notes = db.Column(
        db.Text,
        nullable=True,
    )

    # If a review becomes more than 30 days overdue,
    # this records when the escalation notification occurred.
    review_escalated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    # Residual risk after controls/treatment.
    residual_likelihood = db.Column(
        db.String(30),
        nullable=True,
    )

    residual_consequence = db.Column(
        db.String(30),
        nullable=True,
    )

    residual_rating = db.Column(
        db.String(30),
        nullable=True,
    )

    # open / monitoring / closed
    status = db.Column(
        db.String(30),
        nullable=False,
        default="open",
    )
    __tablename__ = "risks"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    likelihood = db.Column(db.String(30))
    consequence = db.Column(db.String(30))
    rating = db.Column(db.String(30))
    treatment = db.Column(db.Text)
    owner_user_id = db.Column(db.String(36))
    review_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="open")

class CorrectiveAction(TimestampMixin, db.Model):
    __tablename__ = "corrective_actions"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    incident_id = db.Column(
        db.String(36),
        nullable=True,
    )

    risk_id = db.Column(
        db.String(36),
        nullable=True,
    )

    assigned_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    title = db.Column(
        db.String(250),
        nullable=False,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    due_date = db.Column(
        db.Date,
        nullable=True,
    )

    # not_started / in_progress / completed
    status = db.Column(
        db.String(30),
        nullable=False,
        default="not_started",
    )

    completed_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    # Completion must be verified before an
    # incident can be closed.
    verification_status = db.Column(
        db.String(30),
        nullable=False,
        default="pending",
    )

    verified_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    verified_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    verification_notes = db.Column(
        db.Text,
        nullable=True,
    )
class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    user_id = db.Column(db.String(36), nullable=False)
    notification_type = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)

class AuditLog(TimestampMixin, db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    user_id = db.Column(db.String(36))
    action = db.Column(db.String(120), nullable=False)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.String(36))
    details = db.Column(db.Text)
