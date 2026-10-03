from flask import Blueprint, render_template
from flask_login import login_required

from app.decorators import admin_required

bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


@bp.get("/")
@login_required
@admin_required
def index():
    return render_template("onboarding/index.html")
