from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app.constants import Roles
from app.extensions import db
from app.models.identity import Membership, Organisation, User
from app.services.tenant import provision_tenant_schema

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        membership = Membership.query.filter_by(user_id=user.id, is_active=True).first()
        if not membership:
            flash("No active organisation membership was found.", "danger")
            return render_template("auth/login.html")

        login_user(user)
        session["organisation_id"] = membership.organisation_id
        flash("Welcome back.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        organisation_name = request.form.get("organisation_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not organisation_name:
            flash("Organisation name is required.", "danger")
            return render_template("auth/register.html")

        if not email:
            flash("Email is required.", "danger")
            return render_template("auth/register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html")

        organisation = Organisation(
            legal_name=organisation_name,
            trading_name=organisation_name,
        )
        user = User(email=email)
        user.set_password(password)

        db.session.add_all([organisation, user])
        db.session.flush()

        membership = Membership(
            organisation_id=organisation.id,
            user_id=user.id,
            role=Roles.ORGANISATION_ADMIN,
        )
        db.session.add(membership)
        db.session.commit()

        # Create the organisation-specific PostgreSQL schema and tenant tables.
        provision_tenant_schema(organisation.id)

        login_user(user)
        session["organisation_id"] = organisation.id
        flash("Account created successfully. Let's set up your organisation.", "success")
        return redirect(url_for("onboarding.index"))

    return render_template("auth/register.html")


@bp.post("/logout")
def logout():
    session.pop("organisation_id", None)
    logout_user()
    return redirect(url_for("auth.login"))
