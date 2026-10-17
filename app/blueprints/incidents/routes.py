from flask import Blueprint, render_template
from flask_login import login_required

from app.services.prototype import current_prototype_role

bp = Blueprint("incidents", __name__, url_prefix="/incidents")


@bp.get("/")
@login_required
def index():
    return render_template("incidents/index.html", role=current_prototype_role())


@bp.get("/new/")
@login_required
def new():
    return render_template("incidents/new.html", role=current_prototype_role())
