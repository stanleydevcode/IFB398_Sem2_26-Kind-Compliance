from app.extensions import db
from app.models.base import TimestampMixin, uuid_str

class Participant(TimestampMixin, db.Model):
    __tablename__ = "participants"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    support_type = db.Column(db.String(150))
    plan_status = db.Column(db.String(50))
    key_worker_staff_id = db.Column(db.String(36))
    care_requirements = db.Column(db.Text)

class ParticipantNote(TimestampMixin, db.Model):
    __tablename__ = "participant_notes"
    __table_args__ = {"schema": "tenant"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    participant_id = db.Column(
        db.String(36),
        db.ForeignKey("tenant.participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_staff_id = db.Column(db.String(36), nullable=False)
    note_type = db.Column(db.String(50), nullable=False)  # progress/handover
    content = db.Column(db.Text, nullable=False)
