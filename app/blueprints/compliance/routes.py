from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import manager_required

bp = Blueprint("compliance", __name__, url_prefix="/compliance")

@bp.get("/")
@login_required
@manager_required
def index():
    return render_template(
        "placeholders/module.html",
        title="Compliance Requirements",
        module_name="compliance",
    )
