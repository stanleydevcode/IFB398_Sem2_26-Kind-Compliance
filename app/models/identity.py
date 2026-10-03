from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager
from app.models.base import TimestampMixin, uuid_str

class Organisation(TimestampMixin, db.Model):
    __tablename__ = "organisations"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    legal_name = db.Column(db.String(200), nullable=False)
    trading_name = db.Column(db.String(200))
    abn = db.Column(db.String(20))
    ndis_registration_number = db.Column(db.String(100))
    status = db.Column(db.String(30), nullable=False, default="active")

class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Membership(TimestampMixin, db.Model):
    __tablename__ = "memberships"
    __table_args__ = (
        db.UniqueConstraint("organisation_id", "user_id", name="uq_membership_org_user"),
        {"schema": "public"},
    )

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    organisation_id = db.Column(
        db.String(36),
        db.ForeignKey("public.organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    organisation = db.relationship("Organisation")
    user = db.relationship("User")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)
