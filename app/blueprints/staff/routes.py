from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import manager_required

bp = Blueprint("staff", __name__, url_prefix="/staff")

@bp.get("/")
@login_required
@manager_required
def index():
    return render_template(
        "staff/index.html",
    )
