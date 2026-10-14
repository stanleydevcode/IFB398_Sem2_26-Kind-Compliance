from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import manager_required
from app.services.frontend import page_context

bp = Blueprint("participants", __name__, url_prefix="/participants")

@bp.get("/")
@login_required
@manager_required
def index():
    context = page_context()
    return render_template(
        "participants/index.html",
        notes=[],
        **context,
    )
