from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint("incidents", __name__, url_prefix="/incidents")

@bp.get("/")
@login_required
def index():
    return render_template(
        "placeholders/module.html",
        title="Incidents & Complaints",
        module_name="incidents",
    )
