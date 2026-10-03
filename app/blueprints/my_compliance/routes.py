from flask import Blueprint, render_template
from flask_login import login_required


bp = Blueprint("my_compliance", __name__, url_prefix="/my-compliance")

@bp.get("/")
@login_required
def index():
    return render_template(
        "placeholders/module.html",
        title="My Compliance",
        module_name="my_compliance",
    )
