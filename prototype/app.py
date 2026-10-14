from flask import Flask, abort, redirect, render_template, url_for

import data

app = Flask(__name__)


@app.context_processor
def inject_globals():
    return {"ROLES": data.ROLES, "NAV": data.NAV, "ORG": data.ORG,
            "TODAY": data.TODAY, "fmt_date": data.fmt_date,
            "NOTIFICATIONS": data.NOTIFICATIONS,
            "STAFF_NOTIFICATIONS": data.STAFF_NOTIFICATIONS, "home_ep": home_ep,
            "search_index": data.search_index,
            "personal_alert": data.personal_alert, "fmt_log": data.fmt_log}


def home_ep(role):
    return "my_compliance" if role == "staff" else "dashboard"


def check_role(role):
    if role not in data.ROLES:
        abort(404)


@app.route("/")
@app.route("/index.html")
def sign_in():
    return render_template("sign_in.html", accounts=data.ROLES)


@app.route("/<role>/")
def home(role):
    check_role(role)
    return redirect(url_for(home_ep(role), role=role))


@app.route("/<role>/dashboard.html")
def dashboard(role):
    check_role(role)
    if role == "staff":
        return redirect(url_for("my_compliance", role=role))
    return render_template(
        "dashboard.html", role=role, active="dashboard",
        readiness=data.READINESS, health=data.health(),
        expiry=data.expiry_monitor(), tasks=data.prioritised_tasks(),
        risks=data.risks_with_status(), owners=data.OWNERS,
        missing_docs=data.document_summary()["missing"],
        counts=data.dashboard_counts(),
        doc_summary=data.document_summary(),
        reportable=data.REPORTABLE,
    )


@app.route("/<role>/documents.html")
def documents(role):
    check_role(role)
    if role == "staff":
        abort(404)
    return render_template(
        "documents.html", role=role, active="documents",
        categories=data.CATEGORIES, category_name=data.CATEGORY_NAME,
        category_counts=data.category_counts(), policies=data.policy_documents(),
        records=data.record_documents(), missing=data.missing_by_module(),
        evidence=data.evidence_gaps(), summary=data.document_summary(),
    )


@app.route("/<role>/documents/<slug>.html")
def document(role, slug):
    check_role(role)
    doc = data.get_document(slug)
    if role == "staff" or not doc:
        abort(404)
    return render_template("document.html", role=role, active="documents", doc=doc,
                           categories=data.CATEGORIES, category_name=data.CATEGORY_NAME,
                           title=doc["title"])


@app.route("/<role>/workers.html", endpoint="staff")
def workers(role):
    check_role(role)
    if role == "staff":
        abort(404)
    return render_template("workers.html", role=role, active="staff", workers=data.workers_by_expiry(),
                           creds=data.CREDS, summary=data.worker_summary(), cred_name=data.CRED_NAME)


@app.route("/<role>/workers/<slug>.html")
def worker(role, slug):
    check_role(role)
    w = data.get_worker(slug)
    if role == "staff" or not w:
        abort(404)
    return render_template("worker.html", role=role, active="staff", w=w, creds=data.CREDS,
                           cred_name=data.CRED_NAME, title=w["name"])


@app.route("/<role>/participants.html")
def participants(role):
    check_role(role)
    return render_template("participants.html", role=role, active="participants",
                           participants=data.participants_for(role), notes=data.notes_for(role),
                           summary=data.participant_summary(role), workers=data.WORKERS)


@app.route("/<role>/participants/<slug>.html")
def participant(role, slug):
    check_role(role)
    p = data.get_participant(slug, role)
    if not p:
        abort(404)
    return render_template("participant.html", role=role, active="participants", p=p,
                           participants=data.participants_for(role), workers=data.WORKERS, title=p["name"])


@app.route("/<role>/incidents.html")
def incidents(role):
    check_role(role)
    return render_template("incidents.html", role=role, active="incidents", cases=data.cases_for(role),
                           summary=data.case_summary(), reportable=data.REPORTABLE)


@app.route("/<role>/incidents/new.html")
def report_incident(role):
    check_role(role)
    return render_template("incident_new.html", role=role, active="incidents", title="Report an incident",
                           participants=data.participants_for(role), categories=data.CATEGORIES_INC,
                           workers=data.WORKERS, risks=data.risks_with_status())


@app.route("/<role>/incidents/<slug>.html")
def case(role, slug):
    check_role(role)
    c = data.get_case(slug)
    if role == "staff" or not c:
        abort(404)
    return render_template("case.html", role=role, active="incidents", c=c, stages=data.STAGES,
                           workers=data.WORKERS, title=c["ref"])


@app.route("/<role>/my-compliance.html")
def my_compliance(role):
    check_role(role)
    return render_template("my_compliance.html", role=role, active="my_compliance", title="My compliance",
                           mc=data.my_compliance(role), creds=data.CREDS, cred_name=data.CRED_NAME)


@app.route("/<role>/workers/<slug>/preview.html")
def worker_preview(role, slug):
    check_role(role)
    w = data.get_worker(slug)
    if role == "staff" or not w or w["login"] != "staff":
        abort(404)
    return render_template("my_compliance.html", role=role, active="staff", title=w["name"],
                           mc=data.my_compliance_for(w["name"]), creds=data.CREDS,
                           cred_name=data.CRED_NAME, preview=True)


@app.route("/<role>/setup.html")
def setup(role):
    check_role(role)
    if role != "admin":
        abort(404)
    chosen = data.SELECTED_GROUPS

    # split the registration groups into the three lists on the page
    selected = []
    other = []
    verification = []
    group_info = {}
    for g in data.REG_GROUPS:
        code, name, pathway, module = g
        group_info[code] = {"name": name, "pw": pathway}
        if code in chosen:
            selected.append(g)
        elif pathway == "cert":
            other.append(g)
        if pathway == "ver":
            verification.append(g)

    counts = data.module_counts()
    modules = {}
    mod_short = {}
    for m, trigger in data.MODULE_TRIGGERS.items():
        modules[m] = {"label": data.MODULE_LABEL[m], "groups": trigger["groups"], "count": counts.get(m, 0)}
        mod_short[m] = m.replace("M", "Module ")

    # values the page needs to recalculate the documents in the browser
    js = {
        "today": data.TODAY.isoformat(),
        "groups": group_info,
        "core": data.CORE_BASELINE,
        "conditional": data.CONDITIONAL_ITEMS,
        "conditional_codes": data.CONDITIONAL_CODES,
        "verification": data.VERIFICATION_BASELINE,
        "core_missing": len(data.CORE_MISSING),
        "modules": modules,
    }
    return render_template(
        "setup.html", role=role, active="setup", steps=data.SETUP_STEPS, done=data.SETUP_DONE,
        org=data.ORG_PROFILE, org_types=data.ORG_TYPES, states=data.STATES,
        insurance=data.INSURANCE, ins_types=data.INSURANCE_TYPES, chosen=chosen,
        selected=selected, other=other, ver=verification, mod_short=mod_short,
        req=data.requirement_total(), missing=len(data.all_missing()),
        people=data.key_personnel(), js=js,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
