from sqlalchemy.orm import synonym

from app.extensions import db
from app.models.base import TimestampMixin, uuid_str


class Participant(TimestampMixin, db.Model):
    __tablename__ = "participants"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str
    )
    first_name = db.Column(
        db.String(120),
        nullable=False
    )
    last_name = db.Column(
        db.String(120),
        nullable=False
    )
    date_of_birth = db.Column(db.Date)
    ndis_number = db.Column(db.String(50), index=True)
    support_type = db.Column(db.String(150))
    plan_status = db.Column(db.String(50))
    plan_start_date = db.Column(db.Date)
    plan_end_date = db.Column(db.Date)
    key_worker_staff_id = db.Column(db.String(36), db.ForeignKey("tenant.staff.id"))
    care_requirements = db.Column(db.Text)
    emergency_contact_name = db.Column(db.String(200))
    emergency_contact_phone = db.Column(db.String(50))

    key_worker = db.relationship("Staff", foreign_keys=[key_worker_staff_id])
    consents = db.relationship(
        "ParticipantConsent", back_populates="participant", cascade="all, delete", passive_deletes=True,
    )
    notes = db.relationship(
        "ParticipantNote", back_populates="participant", cascade="all, delete", passive_deletes=True,
    )
    service_agreements = db.relationship("ServiceAgreement", back_populates="participant")
    cases = db.relationship("Case", back_populates="participant")


class ParticipantConsent(TimestampMixin, db.Model):
    __tablename__ = "participant_consents"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    participant_id = db.Column(
        db.String(36), db.ForeignKey("tenant.participants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    recorded_by = db.Column(db.String(36), db.ForeignKey("public.users.id"))
    consent_type = db.Column(db.String(80), nullable=False)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="granted")
    granted_at = db.Column(db.DateTime(timezone=True))
    expires_at = db.Column(db.DateTime(timezone=True))
    withdrawn_at = db.Column(db.DateTime(timezone=True))
    # Existing date-only and attachment fields remain available.
    date_given = db.Column(db.Date)
    review_date = db.Column(db.Date)
    storage_key = db.Column(db.String(500))
    notes = db.Column(db.Text)

    scope = synonym("purpose")
    recorded_by_user_id = synonym("recorded_by")
    participant = db.relationship("Participant", back_populates="consents")
    recorder = db.relationship("User")


class ParticipantNote(TimestampMixin, db.Model):
    __tablename__ = "participant_notes"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    participant_id = db.Column(
        db.String(36), db.ForeignKey("tenant.participants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    staff_id = db.Column(db.String(36), db.ForeignKey("tenant.staff.id"), nullable=False)
    note_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)

    author_staff_id = synonym("staff_id")
    participant = db.relationship("Participant", back_populates="notes")
    staff = db.relationship("Staff")


class ServiceAgreement(TimestampMixin, db.Model):
    __tablename__ = "service_agreements"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    participant_id = db.Column(
        db.String(36), db.ForeignKey("tenant.participants.id"), nullable=False, index=True,
    )
    document_id = db.Column(db.String(36), db.ForeignKey("tenant.documents.id"), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(30), nullable=False, default="draft")

    participant = db.relationship("Participant", back_populates="service_agreements")
    document = db.relationship("Document")
