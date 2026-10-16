from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import Participant, Staff, ParticipantNote
from app.services import record_pages as pages
from app.services.permissions import can
from app.services.migration.engine import audit
from app.services.migration.reader import MigrationError

bp = Blueprint("participants", __name__, url_prefix="/participants")
pages.install_guards(bp)


def register(assigned=False):
    tenant = g.records_db
    query = select(Participant).options(selectinload(Participant.key_worker))
    if assigned:
        worker = pages.own_staff(tenant)
        query = query.where(Participant.key_worker_staff_id == worker.id) if worker else query.where(False)
    else:
        pages.manager()
    search = request.args.get("q", "").strip()[:100]
    if search:
        query = query.where(((Participant.first_name + " " + Participant.last_name).icontains(search,autoescape=True)) |
                            Participant.ndis_number.icontains(search,autoescape=True))
    tab = request.args.get("tab", "people")
    if tab not in {"people", "notes"}:
        abort(400)
    # Reuse the authorised participant query so assigned staff cannot see others' notes.
    people = []
    notes = []
    last_notes = {}
    if tab == "notes":
        note_query = select(ParticipantNote).options(selectinload(ParticipantNote.participant),
            selectinload(ParticipantNote.staff)).where(ParticipantNote.participant_id.in_(
            query.with_only_columns(Participant.id))).order_by(ParticipantNote.created_at.desc(), ParticipantNote.id)
        notes, number, more = pages.paginate(tenant, note_query)
    else:
        people, number, more = pages.paginate(tenant, query.order_by(
            Participant.last_name, Participant.first_name, Participant.id))
        if people:
            last_notes = dict(tenant.execute(select(ParticipantNote.participant_id,
                func.max(ParticipantNote.created_at)).where(ParticipantNote.participant_id.in_(
                [person.id for person in people])).group_by(ParticipantNote.participant_id)).all())
    return render_template("participants/index.html", participants=people, notes=notes, tab=tab,
                           last_notes=last_notes, page=number, more=more, search=search, assigned=assigned)


@bp.get("/")
@pages.page
def index():
    return register()


@bp.get("/assigned")
@pages.page
def assigned():
    return register(assigned=True)


@bp.get("/<participant_id>")
@pages.page
def detail(participant_id):
    participant = pages.participant_or_404(participant_id)
    tenant = g.records_db
    notes = tenant.scalars(select(ParticipantNote).where(ParticipantNote.participant_id == participant.id)
                           .order_by(ParticipantNote.created_at.desc()).limit(50)).all()
    return render_template("participants/detail.html", participant=participant, notes=notes,
        evidence=pages.linked_evidence(tenant,"participant",participant.id),
        sources=pages.provenance(tenant,"participant",participant.id) if g.records_member.role in pages.MANAGERS else [])


@bp.route("/<participant_id>/edit", methods=["GET", "POST"])
@pages.page
def edit(participant_id):
    pages.manager()
    tenant = g.records_db
    participant = pages.record(Participant,participant_id)
    if request.method == "POST":
        reason = pages.checked_revision(participant)
        fields = ["first_name","last_name","date_of_birth","ndis_number","support_type","plan_status",
                  "plan_start_date","plan_end_date","emergency_contact_name","emergency_contact_phone"]
        if can(g.records_member.role,"edit_participant_care_requirements"):
            fields.append("care_requirements")
        elif request.form.get("care_requirements",participant.care_requirements or "") != (participant.care_requirements or ""):
            abort(403)
        changed = pages.save_profile(tenant,participant,"participant",fields)
        key_worker = request.form.get("key_worker_staff_id") or None
        if key_worker:
            worker = tenant.get(Staff,key_worker)
            if not worker or (not worker.is_active and key_worker != participant.key_worker_staff_id):
                raise MigrationError("Choose an active worker in this organisation.")
        if participant.key_worker_staff_id != key_worker:
            participant.key_worker_staff_id = key_worker
            changed.append("key_worker_staff_id")
        audit(tenant,current_user.id,"participant.updated","participant",participant.id,{"fields":changed,"reason":reason})
        flash("Participant details and key worker saved.","success")
        return redirect(url_for("participants.detail",participant_id=participant.id))
    workers = tenant.scalars(select(Staff).where(Staff.is_active.is_(True) | (Staff.id == participant.key_worker_staff_id)).order_by(Staff.last_name,Staff.first_name)).all()
    return render_template("participants/edit.html",participant=participant,workers=workers)


@bp.get("/<participant_id>/evidence/<version_id>")
@pages.page
def evidence_download(participant_id,version_id):
    participant = pages.participant_or_404(participant_id)
    allowed = pages.linked_evidence(g.records_db,"participant",participant.id)
    if not any(x["version"].id == version_id for x in allowed):
        abort(404)
    return pages.download_version(g.records_db,version_id)
