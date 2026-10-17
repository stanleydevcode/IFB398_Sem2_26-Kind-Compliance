from sqlalchemy.orm import synonym

from app.extensions import db
from app.models.base import TimestampMixin, uuid_str, utcnow


class Case(TimestampMixin, db.Model):
    __tablename__ = "cases"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    reference = db.Column(db.String(50), unique=True)
    reported_by_staff_id = db.Column(db.String(36), db.ForeignKey("tenant.staff.id"))
    participant_id = db.Column(db.String(36), db.ForeignKey("tenant.participants.id"))
    assigned_membership_id = db.Column(db.String(36), db.ForeignKey("public.memberships.id"))
    reportability_decided_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    closed_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    case_type = db.Column(db.String(50), nullable=False, default="incident")
    category = db.Column(db.String(80), nullable=False)
    occurred_at = db.Column(db.DateTime(timezone=True))
    reported_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    reportable_to_ndis = db.Column(db.Boolean)
    reportability_decided_at = db.Column(db.DateTime(timezone=True))
    commission_reference = db.Column(db.String(100))
    status = db.Column(db.String(40), nullable=False, default="reported")
    severity = db.Column(db.String(30))
    priority = db.Column(db.String(30))
    description = db.Column(db.Text, nullable=False)
    immediate_response = db.Column(db.Text)
    closed_at = db.Column(db.DateTime(timezone=True))
    imported_at = db.Column(db.DateTime(timezone=True))
    location = db.Column(db.String(250))
    investigation_notes = db.Column(db.Text)
    outcome = db.Column(db.Text)
    # Preserve the existing workflow's additional audit details.
    assigned_user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    reportability_reason = db.Column(db.Text)
    commission_reference_recorded_by_user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    commission_reference_recorded_at = db.Column(db.DateTime(timezone=True))
    closure_notes = db.Column(db.Text)

    reportable = synonym("reportable_to_ndis")
    reportability_decided_by_user_id = synonym("reportability_decided_by")
    closed_by_user_id = synonym("closed_by")
    reporter = db.relationship("Staff", foreign_keys=[reported_by_staff_id])
    participant = db.relationship("Participant", back_populates="cases")
    assigned_membership = db.relationship("Membership")
    reportability_decider = db.relationship("User", foreign_keys=[reportability_decided_by])
    closer = db.relationship("User", foreign_keys=[closed_by])
    corrective_actions = db.relationship("CorrectiveAction", back_populates="case")


# Existing imports continue to use the ERD's cases model.
IncidentCase = Case


class Risk(TimestampMixin, db.Model):
    __tablename__ = "risks"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    owner_staff_id = db.Column(db.String(36), db.ForeignKey("tenant.staff.id"))
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    likelihood = db.Column(db.Integer)
    consequence = db.Column(db.Integer)
    rating = db.Column(db.String(30))
    treatment = db.Column(db.Text)
    review_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="open")
    residual_rating = db.Column(db.String(30))
    existing_controls = db.Column(db.Text)
    owner_user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    last_reviewed_at = db.Column(db.DateTime(timezone=True))
    last_reviewed_by_user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    review_notes = db.Column(db.Text)
    review_escalated_at = db.Column(db.DateTime(timezone=True))
    residual_likelihood = db.Column(db.String(30))
    residual_consequence = db.Column(db.String(30))

    owner = db.relationship("Staff")
    controls = db.relationship("RiskControl", back_populates="risk")
    corrective_actions = db.relationship("CorrectiveAction", back_populates="risk")


class RiskControl(TimestampMixin, db.Model):
    __tablename__ = "risk_controls"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    risk_id = db.Column(db.String(36), db.ForeignKey("tenant.risks.id"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    control_type = db.Column(db.String(80))

    risk = db.relationship("Risk", back_populates="controls")


class CorrectiveAction(TimestampMixin, db.Model):
    __tablename__ = "corrective_actions"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    assigned_membership_id = db.Column(db.String(36), db.ForeignKey("public.memberships.id"))
    risk_id = db.Column(db.String(36), db.ForeignKey("tenant.risks.id"))
    case_id = db.Column(db.String(36), db.ForeignKey("tenant.cases.id"))
    verified_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    due_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="not_started")
    description = db.Column(db.Text)
    verified_at = db.Column(db.DateTime(timezone=True))
    assigned_user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    title = db.Column(db.String(250))
    completed_at = db.Column(db.DateTime(timezone=True))
    verification_status = db.Column(db.String(30), nullable=False, default="pending")
    verification_notes = db.Column(db.Text)

    incident_id = synonym("case_id")
    verified_by_user_id = synonym("verified_by")
    assigned_membership = db.relationship("Membership")
    risk = db.relationship("Risk", back_populates="corrective_actions")
    case = db.relationship("Case", back_populates="corrective_actions")
    verifier = db.relationship("User", foreign_keys=[verified_by])


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"), nullable=False)
    type = db.Column(db.String(80), nullable=False)
    related_entity_type = db.Column(db.String(80))
    related_entity_id = db.Column(db.String(36))
    due_date = db.Column(db.Date)
    channel = db.Column(db.String(30))
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    message = db.Column(db.Text)

    notification_type = synonym("type")
    user = db.relationship("User")


class AuditLog(TimestampMixin, db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    user_id = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    action = db.Column(db.String(120), nullable=False)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.String(36))
    changes = db.Column(db.JSON)
    # Legacy free-text audit messages are distinct from structured changes.
    details = db.Column(db.Text)

    user = db.relationship("User")
