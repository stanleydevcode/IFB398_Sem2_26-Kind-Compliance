from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import synonym
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager
from app.models.base import TimestampMixin, uuid_str
from app.services.tenant import schema_name_for_organisation


def default_schema_name(context):
    return schema_name_for_organisation(context.get_current_parameters()["id"])


class Organisation(TimestampMixin, db.Model):
    __tablename__ = "organisations"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    legal_name = db.Column(db.String(200), nullable=False)
    trading_name = db.Column(db.String(200))
    abn = db.Column(db.String(20))
    ndis_registration_number = db.Column(db.String(100))
    schema_name = db.Column(db.String(63), unique=True, nullable=False, default=default_schema_name)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    operating_rules = db.Column(db.JSON, nullable=False, default=dict)
    status = db.Column(db.String(30), nullable=False, default="active")

    memberships = db.relationship(
        "Membership", back_populates="organisation", cascade="all, delete", passive_deletes=True,
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_active_account = synonym("is_active")
    last_login_at = db.Column(db.DateTime(timezone=True))

    memberships = db.relationship(
        "Membership", back_populates="user", cascade="all, delete", passive_deletes=True,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Role(TimestampMixin, db.Model):
    __tablename__ = "roles"
    __table_args__ = {"schema": "public"}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(250))

    memberships = db.relationship("Membership", back_populates="role_record")


class Membership(TimestampMixin, db.Model):
    __tablename__ = "memberships"
    __table_args__ = (
        db.UniqueConstraint("organisation_id", "user_id", name="uq_membership_org_user"),
        {"schema": "public"},
    )

    id = db.Column(db.String(36), primary_key=True, default=uuid_str)
    organisation_id = db.Column(
        db.String(36), db.ForeignKey("public.organisations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id = db.Column(
        db.String(36), db.ForeignKey("public.users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role_id = db.Column(db.Integer, db.ForeignKey("public.roles.id"), nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    organisation = db.relationship("Organisation", back_populates="memberships")
    user = db.relationship("User", back_populates="memberships")
    role_record = db.relationship("Role", back_populates="memberships")

    # Keep the role-name API consumed by decorators and dashboard templates.
    @hybrid_property
    def role(self):
        return self.role_record.name if self.role_record is not None else None

    @role.expression
    def role(cls):
        return db.select(Role.name).where(Role.id == cls.role_id).scalar_subquery()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)
