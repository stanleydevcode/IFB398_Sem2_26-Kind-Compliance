from app.extensions import db
from app.models.base import TimestampMixin, uuid_str


class Participant(TimestampMixin, db.Model):
    __tablename__ = "participants"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    first_name = db.Column(
        db.String(120),
        nullable=False,
    )

    last_name = db.Column(
        db.String(120),
        nullable=False,
    )

    # Sensitive participant information.
    date_of_birth = db.Column(
        db.Date,
        nullable=True,
    )

    ndis_number = db.Column(
        db.String(50),
        nullable=True,
        index=True,
    )

    support_type = db.Column(
        db.String(150),
        nullable=True,
    )

    plan_status = db.Column(
        db.String(50),
        nullable=True,
    )

    key_worker_staff_id = db.Column(
        db.String(36),
        nullable=True,
    )

    # Only Compliance Managers will be allowed
    # to edit this through the application.
    care_requirements = db.Column(
        db.Text,
        nullable=True,
    )

    emergency_contact_name = db.Column(
        db.String(200),
        nullable=True,
    )

    emergency_contact_phone = db.Column(
        db.String(50),
        nullable=True,
    )


class ParticipantConsent(TimestampMixin, db.Model):
    __tablename__ = "participant_consents"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    participant_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "tenant.participants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Examples:
    # collect_information
    # use_information
    # disclose_information
    consent_type = db.Column(
        db.String(80),
        nullable=False,
    )

    # granted / withdrawn / expired
    status = db.Column(
        db.String(30),
        nullable=False,
        default="granted",
    )

    date_given = db.Column(
        db.Date,
        nullable=True,
    )

    review_date = db.Column(
        db.Date,
        nullable=True,
    )

    # Describes what the participant agreed to.
    scope = db.Column(
        db.Text,
        nullable=True,
    )

    recorded_by_user_id = db.Column(
        db.String(36),
        nullable=True,
    )

    withdrawn_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )

    # Optional signed consent form or evidence.
    storage_key = db.Column(
        db.String(500),
        nullable=True,
    )

    notes = db.Column(
        db.Text,
        nullable=True,
    )


class ParticipantNote(TimestampMixin, db.Model):
    __tablename__ = "participant_notes"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=uuid_str,
    )

    participant_id = db.Column(
        db.String(36),
        db.ForeignKey(
            "tenant.participants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    author_staff_id = db.Column(
        db.String(36),
        nullable=False,
    )

    note_type = db.Column(
        db.String(50),
        nullable=False,
    )

    content = db.Column(
        db.Text,
        nullable=False,
    )