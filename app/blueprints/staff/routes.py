from flask import Blueprint, render_template, session
from flask_login import login_required

from app.decorators import manager_required
from app.models.workforce import Staff
from app.services.frontend import page_context
from app.services.tenant import tenant_session

bp = Blueprint("staff", __name__, url_prefix="/staff")


@bp.get("/")
@login_required
@manager_required
def index():
    context = page_context()

    with tenant_session(session.get("organisation_id")) as tenant_db:
        staff_records = (
            tenant_db.query(Staff)
            .order_by(Staff.first_name, Staff.last_name)
            .all()
        )

        workers = []

        for staff in staff_records:
            workers.append(
                {
                    "name": f"{staff.first_name} {staff.last_name}",
                    "initials": (
                        f"{staff.first_name[:1]}{staff.last_name[:1]}"
                    ).upper(),
                    "position": staff.job_title or "—",
                    "fields": {
                        "email": staff.email or "",
                    },
                    "credentials": [],
                    "blocked": False,
                    "status": "No credentials recorded",
                    "status_tone": "warn",
                }
            )

    counts = {
        "active": len(staff_records),
        "ok": 0,
        "soon": 0,
        "blocked": 0,
    }

    context["workers"] = workers
    context["pending"] = []
    context["counts"] = counts

    return render_template(
        "staff/index.html",
        **context,
    )