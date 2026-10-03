from flask import Blueprint, render_template
from flask_login import login_required

from app.decorators import current_membership

bp = Blueprint("dashboard", __name__)

@bp.get("/")
@login_required
def index():
    membership = current_membership()
    return render_template(
        "dashboard/index.html",
        membership=membership,
    )
