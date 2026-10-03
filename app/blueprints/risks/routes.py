from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import manager_required

bp = Blueprint("risks", __name__, url_prefix="/risks")

@bp.get("/")
@login_required
@manager_required
def index():
    return render_template(
        "placeholders/module.html",
        title="Risk Register",
        module_name="risks",
    )
