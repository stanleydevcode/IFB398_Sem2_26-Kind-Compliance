from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_required

from app.services.prototype import current_prototype_role

bp = Blueprint("dashboard", __name__)


@bp.get("/")
@login_required
def index():
    if current_prototype_role() == "staff":
        return redirect(url_for("my_compliance.index"))
    return render_template("dashboard/index.html")
