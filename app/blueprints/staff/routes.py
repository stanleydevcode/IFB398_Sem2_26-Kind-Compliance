from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import manager_required
from app.services.frontend import page_context

bp = Blueprint("staff", __name__, url_prefix="/staff")

@bp.get("/")
@pages.page
def index():
    context = page_context()
    return render_template(
        "staff/index.html",
        pending=[],
        counts=dict(active="—", ok="—", soon="—", blocked="—"),
        **context,
    )
