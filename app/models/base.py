from datetime import datetime, timezone
import uuid

from app.extensions import db

def uuid_str():
    return str(uuid.uuid4())

def utcnow():
    return datetime.now(timezone.utc)

class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
