from app.extensions import db
from app.models.base import TimestampMixin, uuid_str

class IncidentCase(TimestampMixin, db.Model):
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

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    incident_id = db.Column(db.String(36))
    risk_id = db.Column(db.String(36))
    assigned_user_id = db.Column(db.String(36))
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="not_started")

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
