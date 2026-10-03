from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import admin_required

bp = Blueprint("migration", __name__, url_prefix="/migration")

@bp.get("/")
@login_required
@admin_required
def index():
    return render_template(
        "placeholders/module.html",
        title="Data Migration",
        module_name="migration",
    )
