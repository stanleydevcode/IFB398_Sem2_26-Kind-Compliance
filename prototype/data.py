# Sample data for the prototype. This will be replaced by the PostgreSQL database.
import re
from datetime import date

# demo date so the numbers stay the same every time
TODAY = date(2026, 9, 27)

ROLES = {
    "admin": {"label": "Organization Administrator", "short": "Administrator",
              "user": "Douglas Okafor", "initials": "DO",
              "email": "d.okafor@brightwatercare.com.au"},
    "manager": {"label": "Compliance Manager", "short": "Compliance Manager",
                "user": "Sarah Chen", "initials": "SC",
                "email": "s.chen@brightwatercare.com.au"},
    "staff": {"label": "Staff Member", "short": "Support Worker",
              "user": "Marcus Webb", "initials": "MW",
              "email": "m.webb@brightwatercare.com.au"},
}

# menu for each role: (endpoint, label)
NAV = {
    "admin": [("dashboard", "Dashboard"), ("documents", "Documents"), ("staff", "Workers"),
              ("participants", "Participants"), ("incidents", "Incidents"), ("setup", "Setup")],
    "manager": [("dashboard", "Dashboard"), ("documents", "Documents"), ("staff", "Workers"),
                ("participants", "Participants"), ("incidents", "Incidents")],
    "staff": [("my_compliance", "My compliance"), ("participants", "Participants"),
              ("incidents", "Incidents")],
}

ORG = {"name": "Brightwater Care", "setup_step": 4, "setup_total": 5}

# ---- scope ----
SELECTED_GROUPS = ["0107", "0104", "0110", "0132", "0136", "0138"]

# which registration groups add which module
MODULE_TRIGGERS = {
    "M1": {"name": "High intensity daily personal activities", "groups": ["0104"]},
    "M2": {"name": "Specialist behaviour support", "groups": ["0110"]},
    "M2A": {"name": "Implementing behaviour support plans", "groups": ["0110"]},
    "M3": {"name": "Early childhood supports", "groups": ["0118"]},
    "M4": {"name": "Specialised support coordination", "groups": ["0132"]},
    "M5": {"name": "Specialist disability accommodation", "groups": ["0131"]},
    "M5A": {"name": "Supported independent living", "groups": ["0138"]},
}

_REQ = [
    ("M1", "High Intensity Daily Personal Activities Policy", "Policy", "Critical"),
    ("M1", "Complex Bowel Care Plan / Procedure", "Procedure", "Critical"),
    ("M1", "Enteral (Naso-Gastric) Feeding & Management Plan / Procedure", "Procedure", "Critical"),
    ("M1", "Tracheostomy Management Plan / Procedure", "Procedure", "Critical"),
    ("M1", "Urinary Catheter Management Plan / Procedure", "Procedure", "Critical"),
    ("M1", "Ventilator Management Plan / Procedure", "Procedure", "Critical"),
    ("M1", "Subcutaneous Injection Plan / Procedure", "Procedure", "Critical"),
    ("M1", "Complex Wound Management Plan / Procedure", "Procedure", "Critical"),
    ("M1", "High Intensity Support Skills Competency Register", "Register", "Critical"),
    ("M1", "Health Practitioner Review Record", "Form", "Critical"),
    ("M1", "High Intensity Incident & Emergency Escalation Form", "Form", "Critical"),
    ("M2", "Behaviour Support Practitioner Suitability & Credentialing Policy", "Policy", "High"),
    ("M2", "Clinical Supervision Policy", "Policy", "High"),
    ("M2", "Functional Behaviour Assessment Procedure", "Procedure", "High"),
    ("M2", "Behaviour Support Plan Development Procedure", "Procedure", "High"),
    ("M2", "Behaviour Support Plan Monitoring & Review Procedure", "Procedure", "High"),
    ("M2", "Interim Behaviour Support Plan Procedure", "Procedure", "High"),
    ("M2", "Reportable Incident (Restrictive Practice Use) Procedure", "Procedure", "High"),
    ("M2", "Behaviour Support Plan Template", "Form", "High"),
    ("M2", "Interim Behaviour Support Plan Template", "Form", "High"),
    ("M2", "Restrictive Practice Authorisation Register", "Register", "High"),
    ("M2", "Behaviour Support Practitioner Professional Development Register", "Register", "High"),
    ("M2", "Behaviour Support Plan Lodgement Record (NDIS Commission)", "Register", "High"),
    ("M2A", "Regulated Restrictive Practices Policy", "Policy", "Critical"),
    ("M2A", "Restrictive Practice Implementation Procedure", "Procedure", "Critical"),
    ("M2A", "Monthly Restrictive Practice Reporting Procedure", "Procedure", "Critical"),
    ("M2A", "Worker Training Record (Safe Use of Restrictive Practices)", "Register", "Critical"),
    ("M2A", "Behaviour Support Plan Implementation Monitoring Form", "Form", "Critical"),
    ("M2A", "Restrictive Practice Incident Register", "Register", "Critical"),
    ("M3", "Family-Centred Practice Policy", "Policy", "High"),
    ("M3", "Evidence-Informed Practice Policy", "Policy", "High"),
    ("M3", "Child Risk of Harm Reporting Procedure", "Procedure", "High"),
    ("M3", "Key Worker Model Procedure", "Procedure", "High"),
    ("M3", "Transition Planning Procedure", "Procedure", "High"),
    ("M3", "Early Childhood Support Plan Template", "Form", "High"),
    ("M3", "Family Engagement & Consent Form", "Form", "High"),
    ("M3", "Early Childhood Outcomes Measurement Record", "Register", "High"),
    ("M4", "Specialised Support Coordination Policy", "Policy", "High"),
    ("M4", "Conflict of Interest Management Procedure (Support Coordination)", "Procedure", "High"),
    ("M4", "Complex Needs Escalation Procedure", "Procedure", "High"),
    ("M4", "Support Coordination Plan Template", "Form", "High"),
    ("M4", "Support Coordinator Caseload Register", "Register", "High"),
    ("M5", "Specialist Disability Accommodation Policy", "Policy", "High"),
    ("M5", "SDA Dwelling Enrolment Procedure", "Procedure", "High"),
    ("M5", "SDA Tenancy Agreement Template", "Form", "High"),
    ("M5", "Maintenance and Repairs Procedure", "Procedure", "High"),
    ("M5", "Vacancy Management Procedure", "Procedure", "High"),
    ("M5", "Conflict of Interest Separation Statement (SDA and SIL)", "Form", "High"),
    ("M5", "SDA Dwelling Register", "Register", "High"),
    ("M5A", "Supported Independent Living Policy", "Policy", "High"),
    ("M5A", "Supported Decision-Making Procedure", "Procedure", "High"),
    ("M5A", "SIL Safeguarding Procedure", "Procedure", "High"),
    ("M5A", "Practice Governance Framework (SIL)", "Policy", "High"),
    ("M5A", "Shared Living Roster of Care Template", "Form", "High"),
    ("M5A", "Tenancy and Housing Agreement Procedure", "Procedure", "High"),
    ("M5A", "Household Compatibility Assessment Form", "Form", "High"),
    ("M5A", "Resident House Meeting Record", "Form", "High"),
    ("M5A", "SIL Quote and Funding Reconciliation Register", "Register", "High"),
    ("M5A", "SIL Property Safety Inspection Register", "Register", "High"),
]
MODULE_REQUIREMENTS = [
    {"module": m, "title": t, "type": ty, "priority": p} for m, t, ty, p in _REQ
]
UPLOADED_TITLES = set()


def missing_documents(groups=None):
    if groups is None:
        groups = SELECTED_GROUPS
    active_modules = []
    for module, info in MODULE_TRIGGERS.items():
        for g in info["groups"]:
            if g in groups and module not in active_modules:
                active_modules.append(module)
    result = []
    for r in MODULE_REQUIREMENTS:
        if r["module"] in active_modules and r["title"] not in UPLOADED_TITLES:
            result.append(r)
    return result


# ---- scores ----
READINESS = {
    "score": 84, "critical_below": 70, "target": 90,
    "components": [
        ("Stage 2 evidence", 30, 78), ("Documents approved", 20, 84),
        ("Requirements met", 20, 91), ("No priority gaps", 15, 80),
        ("No overdue actions", 10, 88), ("Internal audit done", 5, 100),
    ],
}
def health():
    base = CORE_BASELINE + CONDITIONAL_ITEMS
    ws = worker_summary()
    parts = [("Baseline documents", base - len(CORE_MISSING), base),
             ("Evidence linked", 61, 90),
             ("Workers compliant", ws["ok"], ws["active"])]
    total = 0
    for label, have, out_of in parts:
        total += have / out_of
    score = round(total / len(parts) * 100)
    return {"score": score, "parts": parts}

# ---- credentials ----
COMPANY_CREDENTIALS = [
    {"type": "Public Liability", "holder": "Company insurance", "expires": date(2026, 10, 23), "kind": "company"},
    {"type": "Professional Indemnity", "holder": "Company insurance", "expires": date(2026, 11, 24), "kind": "company"},
]


def expiry_monitor():
    # worker credentials + company insurance expiring in the next 60 days
    rows = []
    for w in WORKERS:
        if w["status"] == "former":
            continue
        for key, exp in w["creds"].items():
            if exp:
                rows.append({"type": CRED_NAME[key], "holder": w["name"], "expires": exp, "kind": "worker",
                             "slug": w["slug"], "pending": bool(w["pending"] and w["pending"]["key"] == key)})
    rows += [dict(c) for c in COMPANY_CREDENTIALS]
    out = []
    for c in rows:
        days = (c["expires"] - TODAY).days
        if days > 60:
            continue
        band = "lapsed" if days < 0 else ("soon" if days <= 30 else "later")
        out.append({**c, "days": days, "band": band})
    out.sort(key=lambda r: r["days"])
    return {
        "rows": out,
        "lapsed": [r for r in out if r["band"] == "lapsed"],
        "soon": [r for r in out if r["band"] == "soon"],
        "later": [r for r in out if r["band"] == "later"],
    }


# ---- tasks ----
SEVERITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
TASKS = [
    {"title": "Upload the Audit Evidence Register", "severity": "Critical", "due": date(2026, 9, 21),
     "owner": "D. Okafor", "points": 2.1, "action": "Upload", "target": "documents"},
    {"title": "Upload the Business Plan", "severity": "Critical", "due": date(2026, 9, 25),
     "owner": "D. Okafor", "points": 1.4, "action": "Upload", "target": "documents"},
    {"title": "Collect Code of Conduct acknowledgements", "severity": "High", "due": date(2026, 9, 27),
     "owner": "S. Chen", "points": 0.8, "action": "Send reminder", "target": "staff",
     "detail": "3 workers haven't acknowledged v4.0"},
    {"title": "Upload 3 First Aid certificates", "severity": "Medium", "due": date(2026, 10, 5),
     "owner": "S. Chen", "points": 1.2, "action": "Open workers", "target": "staff"},
    {"title": "Finish Module 4 self-assessment", "severity": "Medium", "due": date(2026, 10, 11),
     "owner": "S. Chen", "points": 3.0, "action": "Resume", "target": "documents",
     "detail": "60% complete"},
    {"title": "Review Privacy Policy v2.1", "severity": "Low", "due": date(2026, 10, 18),
     "owner": "S. Chen", "points": 0.6, "action": "Start review", "target": "documents"},
    {"title": "Schedule annual internal audit", "severity": "Low", "due": date(2026, 11, 11),
     "owner": "D. Okafor", "points": 0.5, "action": "Schedule", "target": "dashboard"},
]


def prioritised_tasks():
    # Mikela: sort by severity first, then days overdue
    out = []
    for t in TASKS:
        overdue = (TODAY - t["due"]).days
        out.append({**t, "overdue": overdue})
    out.sort(key=lambda t: (SEVERITY_RANK[t["severity"]], -t["overdue"]))
    return out


# ---- risks ----
RISKS = [
    {"ref": "RSK-2026-0064", "name": "Unauthorised use of restrictive practice", "rating": "High",
     "treatment": "Monthly restrictive practice reporting and staff briefing",
     "owner": "S. Chen", "review": date(2026, 8, 20), "working": True},
    {"ref": "RSK-2026-0114", "name": "Participant aggression", "rating": "High",
     "treatment": "Behaviour support plan review and de-escalation training",
     "owner": "P. Nair", "review": date(2026, 9, 12), "working": True},
    {"ref": "RSK-2026-0079", "name": "Participant funds handling", "rating": "High",
     "treatment": "Two-signature petty cash and monthly reconciliation",
     "owner": "D. Okafor", "review": date(2026, 10, 15), "working": True},
    {"ref": "RSK-2026-0087", "name": "Lone working on community access", "rating": "Medium",
     "treatment": "Check-in schedule and duress app rollout",
     "owner": "S. Chen", "review": date(2026, 10, 30), "working": False},
    {"ref": "RSK-2026-0102", "name": "Medication administration", "rating": "Medium",
     "treatment": "Webster pack audit and double-sign check",
     "owner": "S. Chen", "review": date(2026, 11, 14), "working": True},
    {"ref": "RSK-2026-0091", "name": "Manual handling", "rating": "Medium",
     "treatment": "Hoist servicing and transfer competency sign-off",
     "owner": "P. Nair", "review": date(2026, 12, 1), "working": True},
]
OWNERS = ["D. Okafor", "S. Chen", "P. Nair", "M. Webb"]


def risks_with_status():
    # overdue reviews stay flagged, more than 30 days overdue = escalated
    out = []
    for r in RISKS:
        overdue = (TODAY - r["review"]).days
        if overdue > 30:
            status = "escalated"
        elif overdue > 0:
            status = "overdue"
        elif not r["working"]:
            status = "monitoring"
        else:
            status = "controlled"
        out.append({**r, "overdue": overdue, "status": status})
    return out


def dashboard_counts():
    open_cases = []
    for c in CASES:
        if c["stage"] != 5:
            open_cases.append(_case(c))
    tasks = prioritised_tasks()

    priority_gaps = 0
    for r in all_missing():
        if r["priority"] == "Critical":
            priority_gaps += 1

    overdue = 0
    open_actions = len(tasks)
    for t in tasks:
        if t["overdue"] > 0:
            overdue += 1
    for c in open_cases:
        overdue += c["overdue_actions"]
        open_actions += c["open_actions"]

    return {"priority_gaps": priority_gaps, "overdue_actions": overdue,
            "open_actions": open_actions, "open_incidents": len(open_cases)}

REPORTABLE = {"ref": "INC-2026-0044", "category": "Serious injury", "participant": "P-1042",
              "reported": "26 Sep 2026, 2:18 pm", "seconds_left": 17 * 3600 + 41 * 60 + 58}

STAFF_NOTIFICATIONS = [
    {"kind": "info", "title": "First Aid renewal sent for verification",
     "body": "Sarah Chen will check it. You can still be deployed until 5 Oct.", "when": "2 days ago"},
]

NOTIFICATIONS = [
    {"kind": "danger", "title": "Daniel Hughes can't be deployed",
     "body": "Police Check lapsed 4 days ago. Daniel, his manager and rostering have been told.",
     "when": "4 days ago"},
    {"kind": "warn", "title": "Public Liability renews in 26 days",
     "body": "Upload the new certificate of currency once CGU issues it.", "when": "Today"},
    {"kind": "info", "title": "Privacy Policy v2.2 awaiting your sign-off",
     "body": "Uploaded by S. Chen. It stays in draft until approved.", "when": "Yesterday"},
]


def fmt_date(d):
    return f"{d.day} {d:%b %Y}"


def fmt_log(d, t):
    # "3:07 pm" -> "2026-09-26 15:07"
    hm, ampm = t.split()
    h, m = hm.split(":")
    h = int(h) % 12
    if ampm == "pm":
        h += 12
    return f"{d.isoformat()} {h:02d}:{m}"


# ---- search ----
_SEARCH = [
    ("Daniel Hughes", "Worker", "staff"), ("Sarah Chen", "Worker", "staff"),
    ("Marcus Webb", "Worker", "staff"), ("Priya Nair", "Worker", "staff"),
    ("Amelia Torres", "Worker", "staff"), ("Liam Petersen", "Worker", "staff"),
    ("Code of Conduct Policy", "Policy", "documents"), ("Privacy and Confidentiality Policy", "Policy", "documents"),
    ("Incident Management Policy", "Policy", "documents"), ("Risk Management Policy", "Policy", "documents"),
    ("Work Health and Safety Policy", "Policy", "documents"), ("Complaints Handling Procedure", "Procedure", "documents"),
    ("Audit Evidence Register", "Register", "documents"), ("Business Plan", "Document", "documents"),
    ("J. Tallis (P-1042)", "Participant", "participants"), ("A. Mercado (P-1088)", "Participant", "participants"),
    ("R. Whitlock (P-1103)", "Participant", "participants"), ("M. Delacroix (P-1130)", "Participant", "participants"),
    ("INC-2026-0044 Serious injury", "Incident", "incidents"), ("INC-2026-0043 Abuse or neglect", "Incident", "incidents"),
]


def search_index(role):
    allowed = []
    for ep, label in NAV[role]:
        allowed.append(ep)
    results = []
    for label, kind, ep in _SEARCH:
        if ep in allowed:
            results.append({"label": label, "kind": kind, "ep": ep})
    return results


# ---- Documents & evidence ----
# document folders
CATEGORIES = [
    ("governance", "Governance & Quality", "bi-bank"),
    ("workforce", "Workforce", "bi-people"),
    ("participants", "Participants", "bi-person-heart"),
    ("incidents", "Incidents & Complaints", "bi-exclamation-triangle"),
    ("risk", "Risk & WHS", "bi-shield-exclamation"),
    ("service", "Service Delivery", "bi-truck"),
    ("improvement", "Continuous Improvement", "bi-graph-up-arrow"),
    ("audit", "Audit & Evidence", "bi-search"),
    ("operations", "Business Operations", "bi-briefcase"),
]
CATEGORY_NAME = {k: n for k, n, _ in CATEGORIES}

# title, type, folder, version, next review, standard, pending version
_POLICIES = [
    ("Code of Conduct Policy", "Policy", "workforce", "4.0", date(2027, 3, 12), "Core: Rights and responsibilities", None),
    ("Participant Rights & Responsibilities Policy", "Policy", "participants", "3.2", date(2027, 2, 4), "Core: Rights and responsibilities", None),
    ("Privacy and Confidentiality Policy", "Policy", "participants", "2.1", date(2026, 11, 18), "Core: Rights and responsibilities", "2.2"),
    ("Violence, Abuse, Neglect & Discrimination-Free Policy", "Policy", "participants", "3.0", date(2027, 1, 22), "Core: Rights and responsibilities", None),
    ("Child Safe / Safeguarding Policy", "Policy", "participants", None, date(2027, 4, 8), "Core: Rights and responsibilities", "1.0"),
    ("Complaints Management Policy", "Policy", "incidents", "3.4", date(2026, 12, 9), "Core: Governance and operational management", None),
    ("Incident Management Policy", "Policy", "incidents", "3.1", date(2027, 8, 24), "Core: Governance and operational management", None),
    ("Feedback Policy", "Policy", "improvement", "2.0", date(2027, 4, 15), "Core: Governance and operational management", None),
    ("Quality Management Policy", "Policy", "governance", "2.5", date(2027, 8, 25), "Core: Governance and operational management", "2.6"),
    ("Governance Policy", "Policy", "governance", "1.8", date(2027, 1, 11), "Core: Governance and operational management", None),
    ("Conflict of Interest Policy", "Policy", "governance", "1.5", date(2026, 12, 3), "Core: Governance and operational management", None),
    ("Financial Governance Policy", "Policy", "governance", "2.2", date(2026, 9, 28), "Core: Governance and operational management", None),
    ("Risk Management Policy", "Policy", "risk", "2.3", date(2026, 10, 30), "Core: Governance and operational management", None),
    ("Work Health and Safety Policy", "Policy", "risk", "1.3", date(2027, 2, 19), "Core: Governance and operational management", "1.4"),
    ("Emergency and Disaster Management Policy", "Policy", "risk", "2.4", date(2026, 10, 6), "Core: Support environment", None),
    ("Waste Management & Infection Control Policy", "Policy", "risk", "1.9", date(2027, 2, 14), "Core: Support environment", None),
    ("Human Resource Management Policy", "Policy", "workforce", "2.0", date(2027, 3, 7), "Core: Governance and operational management", None),
    ("Information Management Policy", "Policy", "operations", "2.0", date(2027, 5, 16), "Core: Governance and operational management", None),
    ("Support Provision / Service Delivery Policy", "Policy", "service", "3.0", date(2027, 1, 21), "Core: Provision of supports", None),
    ("Transitions To/From the Provider Policy", "Policy", "service", "2.1", date(2027, 6, 12), "Core: Provision of supports", None),
    ("Medication Management Policy", "Policy", "service", None, date(2027, 9, 30), "Core: Provision of supports", "1.0"),
    ("Participant Money and Property Policy", "Policy", "participants", "1.3", date(2026, 11, 2), "Core: Support environment", None),
    ("Incident Reporting Procedure", "Procedure", "incidents", "3.0", date(2027, 8, 24), "Core: Governance and operational management", None),
    ("Complaints Handling Procedure", "Procedure", "incidents", "2.5", date(2026, 12, 9), "Core: Governance and operational management", None),
    ("Staff Recruitment & Screening Procedure", "Procedure", "workforce", "2.2", date(2027, 3, 7), "Core: Governance and operational management", None),
    ("Staff Onboarding & Induction Procedure", "Procedure", "workforce", "2.0", date(2027, 3, 7), "Core: Governance and operational management", None),
    ("Participant Intake & Onboarding Procedure", "Procedure", "participants", "1.7", date(2027, 1, 21), "Core: Provision of supports", None),
    ("Service Agreement Development Procedure", "Procedure", "service", "1.4", date(2027, 1, 21), "Core: Provision of supports", None),
    ("Support Planning Procedure", "Procedure", "service", "2.3", date(2027, 3, 17), "Core: Provision of supports", None),
    ("Records Retention & Disposal Procedure", "Procedure", "operations", "1.6", date(2027, 5, 16), "Core: Governance and operational management", None),
    ("Emergency Response Procedure", "Procedure", "risk", "2.4", date(2026, 10, 6), "Core: Support environment", None),
    ("Medication Administration Procedure", "Procedure", "service", None, date(2027, 9, 30), "Core: Provision of supports", "1.0"),
]

# forms and registers (no sign-off needed)
_RECORDS = [
    ("Incident Report Form", "Form", "incidents", 42, date(2026, 9, 26), None),
    ("Complaint / Feedback Form", "Form", "incidents", 23, date(2026, 9, 22), None),
    ("Risk Assessment Form", "Form", "risk", 63, date(2026, 9, 25), None),
    ("Staff Screening Checklist", "Form", "workforce", 12, date(2026, 9, 18), None),
    ("Worker Orientation Completion Record", "Form", "workforce", 12, date(2026, 8, 30), None),
    ("Service Agreement Template", "Form", "service", 24, date(2026, 9, 20), None),
    ("Participant Intake Form", "Form", "participants", 19, date(2026, 9, 21), None),
    ("Consent Form", "Form", "participants", 31, date(2026, 9, 23), None),
    ("Support Plan Template", "Form", "service", 19, date(2026, 9, 24), None),
    ("Conflict of Interest Declaration Form", "Form", "governance", 27, date(2026, 9, 12), None),
    ("Incident Register", "Register", "incidents", 42, date(2026, 9, 26), "Incident Report Form"),
    ("Risk Register", "Register", "risk", 17, date(2026, 9, 25), "Risk Assessment Form"),
    ("Staff Training Register", "Register", "workforce", 118, date(2026, 8, 30), "Worker Orientation Completion Record"),
    ("Continuous Improvement Register", "Register", "improvement", 29, date(2026, 9, 19), "Complaint / Feedback Form"),
    ("Medication Chart / Register", "Register", "service", 0, None, None),
]

DRIVES = {
    "Incident Management Policy": ["Incident Register", "Incident Report Form"],
    "Incident Reporting Procedure": ["Incident Register", "Incident Report Form"],
    "Risk Management Policy": ["Risk Register", "Risk Assessment Form"],
    "Complaints Management Policy": ["Complaint / Feedback Form", "Continuous Improvement Register"],
    "Complaints Handling Procedure": ["Complaint / Feedback Form"],
    "Feedback Policy": ["Complaint / Feedback Form", "Continuous Improvement Register"],
    "Human Resource Management Policy": ["Staff Training Register", "Staff Screening Checklist"],
    "Staff Recruitment & Screening Procedure": ["Staff Screening Checklist"],
    "Staff Onboarding & Induction Procedure": ["Worker Orientation Completion Record", "Staff Training Register"],
    "Participant Intake & Onboarding Procedure": ["Participant Intake Form", "Consent Form"],
    "Privacy and Confidentiality Policy": ["Consent Form"],
    "Service Agreement Development Procedure": ["Service Agreement Template"],
    "Support Planning Procedure": ["Support Plan Template"],
    "Conflict of Interest Policy": ["Conflict of Interest Declaration Form"],
    "Medication Management Policy": ["Medication Chart / Register"],
}

MAPS_TO = {
    "Incident Management Policy": [
        ("Core: Governance and operational management", "Incident management", "This policy", "linked"),
        ("Core: Governance and operational management", "Reportable incidents", "Incident Register", "linked"),
        ("Core: Rights and responsibilities", "Complaints and feedback", None, "missing"),
    ],
}


def _slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _doc_status(review, pending, version):
    if pending:
        return "signoff"
    if review and review < TODAY:
        return "overdue"
    if review and (review - TODAY).days <= 60:
        return "due"
    return "current"


def policy_documents():
    docs = []
    for title, typ, cat, ver, review, std, pending in _POLICIES:
        docs.append({
            "slug": _slug(title), "title": title, "type": typ, "category": cat,
            "version": ver, "pending": pending, "review": review, "standard": std,
            "owner": "S. Chen", "cadence": "Annual",
            "status": _doc_status(review, pending, ver),
        })
    return docs


def record_documents():
    out = []
    for title, typ, cat, entries, last, source in _RECORDS:
        out.append({"slug": _slug(title), "title": title, "type": typ, "category": cat,
                    "entries": entries, "last": last, "source": source,
                    "status": "active" if entries else "empty"})
    return out


def get_document(slug):
    for d in policy_documents():
        if d["slug"] != slug:
            continue
        d = dict(d)
        # make up a short version history from the current version number
        history = []
        if d["version"]:
            major = int(d["version"].split(".")[0])
            minor = int(d["version"].split(".")[1])
            versions = [f"{major}.{minor}"]
            if minor > 0:
                versions.append(f"{major}.{minor - 1}")
                if major > 1:
                    versions.append(f"{major - 1}.0")
            elif major > 1:
                versions.append(f"{major - 1}.0")
            dates = [date(2026, 8, 24), date(2026, 2, 12), date(2025, 3, 3)]
            authors = ["S. Chen", "D. Okafor", "D. Okafor"]
            for i in range(len(versions)):
                history.append({"version": versions[i], "approved": dates[i],
                                "author": authors[i], "current": i == 0})
        d["history"] = history

        if d["title"] in MAPS_TO:
            d["maps_to"] = MAPS_TO[d["title"]]
        else:
            short = d["title"].replace(" Policy", "").replace(" Procedure", "")
            d["maps_to"] = [(d["standard"], short, "This document", "linked")]

        d["drives"] = []
        for r in record_documents():
            if r["title"] in DRIVES.get(d["title"], []):
                d["drives"].append(r)
        d["uploaded_by"] = "S. Chen"
        d["uploaded_on"] = date(2026, 9, 24)
        return d
    return None


# core documents that are missing
CORE_MISSING = [
    {"module": "Core", "title": "Business Plan", "type": "Policy", "priority": "Critical", "category": "operations"},
    {"module": "Core", "title": "Audit Evidence Register", "type": "Register", "priority": "Critical", "category": "audit"},
]
MODULE_CATEGORY = {"M1": "service", "M2": "service", "M2A": "service", "M3": "participants",
                   "M4": "service", "M5": "operations", "M5A": "service"}
MODULE_LABEL = {
    "Core": "Core module", "M1": "Module 1: High intensity daily personal activities (0104)",
    "M2": "Module 2: Specialist behaviour support (0110)", "M2A": "Module 2A: Implementing behaviour support plans (0110)",
    "M3": "Module 3: Early childhood supports (0118)",
    "M4": "Module 4: Specialised support coordination (0132)",
    "M5": "Module 5: Specialist disability accommodation (0131)",
    "M5A": "Module 5A: Supported independent living (0138)",
}
PRIORITY_RANK = {"Critical": 0, "High": 1, "Normal": 2}


def all_missing():
    rows = list(CORE_MISSING)
    for r in missing_documents():
        row = dict(r)
        row["category"] = MODULE_CATEGORY.get(r["module"], "operations")
        rows.append(row)
    return rows


def missing_by_module():
    groups = {}
    for r in all_missing():
        if r["module"] not in groups:
            groups[r["module"]] = []
        groups[r["module"]].append(r)

    result = []
    for module, rows in groups.items():
        # the group's priority is its most serious document
        best = "Normal"
        for r in rows:
            if PRIORITY_RANK[r["priority"]] < PRIORITY_RANK[best]:
                best = r["priority"]
        result.append({"module": module, "label": MODULE_LABEL.get(module, module),
                       "rows": rows, "priority": best})
    result.sort(key=lambda g: PRIORITY_RANK[g["priority"]])
    return result


EVIDENCE_GAPS = [
    ("Core: Governance and operational management", "Risk management", "Annual review log for the Risk Management Policy", "missing"),
    ("Core: Governance and operational management", "Incident management", "Implementation log showing the policy in use", "missing"),
    ("Core: Governance and operational management", "Quality management", "Internal audit report from the last 12 months", "missing"),
    ("Core: Governance and operational management", "Information management", "Records retention schedule sign-off", "expired"),
    ("Core: Governance and operational management", "Human resource management", "Performance review records for 2026", "missing"),
    ("Core: Rights and responsibilities", "Complaints and feedback", "Complaints register entries linked to outcomes", "missing"),
    ("Core: Rights and responsibilities", "Privacy and dignity", "Signed consent for each active participant", "partial"),
    ("Core: Rights and responsibilities", "Violence, abuse, neglect", "Staff training record for safeguarding", "expired"),
    ("Core: Provision of supports", "Support planning", "Support plan reviews for 2 participants", "missing"),
    ("Core: Provision of supports", "Service agreements", "Signed agreement for P-1130", "missing"),
    ("Core: Provision of supports", "Responsive support provision", "Service delivery notes sample", "partial"),
    ("Core: Support environment", "Emergency and disaster management", "Evacuation drill record", "expired"),
    ("Core: Support environment", "Management of medication", "Medication competency for 3 workers", "missing"),
    ("Core: Support environment", "Safe environment", "Site safety inspection", "missing"),
]


def evidence_gaps():
    result = []
    for standard, requirement, evidence, status in EVIDENCE_GAPS:
        result.append({"standard": standard, "requirement": requirement,
                       "evidence": evidence, "status": status})
    return result


def document_summary():
    signoff = 0
    due = 0
    for d in policy_documents():
        if d["status"] == "signoff":
            signoff += 1
        if d["status"] == "due" or d["status"] == "overdue":
            due += 1
    return {"missing": len(all_missing()), "signoff": signoff, "due": due,
            "evidence": len(EVIDENCE_GAPS)}


def category_counts():
    counts = {}
    for key, name, icon in CATEGORIES:
        counts[key] = 0
    for d in policy_documents() + record_documents():
        counts[d["category"]] += 1
    return counts


# ---- Workers ----
CREDS = [
    ("screening", "NDIS Worker Screening", "NDIS Commission"),
    ("police", "Police Check", "National Police Check"),
    ("bluecard", "Blue Card", "Queensland Government"),
    ("firstaid", "First Aid", "HLTAID011"),
]
CRED_NAME = {k: n for k, n, _ in CREDS}

_W = [
    # name, position, employment, start date, login, (screening, police, blue card, first aid), pending renewal
    ("Daniel Hughes", "Support Worker", "Casual", date(2025, 2, 10), None,
     (date(2028, 6, 14), date(2026, 9, 23), date(2027, 2, 2), date(2027, 8, 19)),
     ("police", date(2029, 9, 25), date(2026, 9, 26))),
    ("Sarah Chen", "Compliance Manager", "Permanent full time", date(2022, 7, 4), "manager",
     (date(2026, 10, 9), date(2028, 1, 21), date(2027, 5, 30), date(2027, 12, 11)), None),
    ("Marcus Webb", "Support Worker", "Permanent part time", date(2024, 3, 4), "staff",
     (date(2028, 4, 7), date(2027, 11, 15), date(2028, 3, 22), date(2026, 10, 5)),
     ("firstaid", date(2029, 9, 24), date(2026, 9, 25))),
    ("Priya Nair", "Team Leader", "Permanent full time", date(2023, 1, 16), "invited",
     (date(2028, 2, 28), date(2028, 7, 3), date(2026, 11, 13), date(2028, 1, 9)), None),
    ("Douglas Okafor", "Director", "Owner", date(2021, 5, 3), "admin",
     (date(2028, 9, 16), date(2028, 5, 5), date(2027, 10, 27), date(2028, 2, 14)), None),
    ("Amelia Torres", "Support Worker", "Casual", date(2026, 6, 1), None,
     (date(2028, 8, 12), date(2027, 6, 30), None, date(2028, 4, 18)), None),
    ("Liam Petersen", "Support Worker", "Permanent part time", date(2024, 9, 9), "staff",
     (date(2027, 10, 25), date(2028, 9, 8), date(2027, 7, 19), date(2028, 3, 2)), None),
    ("Ruby Nguyen", "Support Worker", "Casual", date(2025, 4, 14), "staff",
     (date(2027, 12, 4), date(2028, 2, 17), date(2028, 6, 11), date(2027, 1, 23)), None),
    ("Ethan Brooks", "Support Worker", "Permanent full time", date(2023, 8, 21), "staff",
     (date(2028, 3, 9), date(2027, 7, 26), date(2028, 4, 15), date(2027, 11, 7)), None),
    ("Chloe Sandhu", "Support Worker", "Casual", date(2025, 11, 3), None,
     (date(2027, 5, 21), date(2028, 10, 2), date(2028, 8, 8), date(2027, 12, 30)), None),
    ("Noah Whitfield", "Support Worker", "Permanent part time", date(2024, 2, 19), "staff",
     (date(2028, 1, 13), date(2028, 4, 29), date(2027, 9, 6), date(2028, 6, 24)), None),
    ("Grace Ellery", "Support Worker", "Casual", date(2026, 3, 30), None,
     (date(2028, 7, 18), date(2027, 11, 1), date(2028, 2, 20), date(2028, 5, 5)), None),
    ("Karen Adeyemi", "Support Worker", "Former employee", date(2022, 2, 7), "deactivated",
     (date(2027, 3, 1), date(2026, 4, 2), date(2027, 8, 1), date(2026, 2, 10)), None),
]

TRAINING = [
    ("Orientation module", date(2025, 2, 12)), ("Manual handling", date(2026, 3, 18)),
    ("Infection control", date(2026, 5, 6)), ("Code of Conduct v4.0 acknowledged", None),
]


def _worker_status(creds, former):
    if former:
        return "former"
    status = "ok"
    for d in creds.values():
        if d is None:
            status = "action"
        elif d < TODAY:
            return "blocked"
        elif (d - TODAY).days <= 30:
            status = "action"
    return status


def _build_workers():
    cred_keys = ["screening", "police", "bluecard", "firstaid"]
    workers = []
    for i, row in enumerate(_W):
        name, pos, emp, start, login, dates, pending = row
        first, last = name.split()
        creds = {}
        for j in range(4):
            creds[cred_keys[j]] = dates[j]
        if pos == "Compliance Manager" or pos == "Director":
            manager = "Douglas Okafor"
        else:
            manager = "Sarah Chen"
        # state of each certificate, used by the filters on the Workers page
        cred_state = {}
        soon = False
        for key, d in creds.items():
            if d is None or d < TODAY:
                cred_state[key] = "bad"
            elif (d - TODAY).days <= 30:
                cred_state[key] = "soon"
                soon = True
            else:
                cred_state[key] = "ok"
        pending_info = None
        if pending:
            pending_info = {"key": pending[0], "new_expiry": pending[1], "uploaded": pending[2]}
        workers.append({
            "slug": _slug(name), "name": name, "initials": first[0] + last[0],
            "position": pos, "employment": emp, "started": start, "login": login,
            "email": first[0].lower() + "." + last.lower() + "@brightwatercare.com.au",
            "phone": f"04{12 + i * 3} {310 + i * 37:03d} {104 + i * 59:03d}",
            "manager": manager, "creds": creds, "cred_state": cred_state, "soon": soon,
            "status": _worker_status(creds, login == "deactivated"),
            "pending": pending_info,
        })
    return workers


WORKERS = _build_workers()


def workers_by_expiry():
    # soonest expiry at the top, a missing certificate counts as today
    def soonest(w):
        if w["status"] == "former":
            return date(2100, 1, 1)
        first = date(2100, 1, 1)
        for d in w["creds"].values():
            if d is None:
                d = TODAY
            if d < first:
                first = d
        return first
    return sorted(WORKERS, key=soonest)


def worker_summary():
    summary = {"active": 0, "ok": 0, "soon": 0, "lapsed": 0, "pending": 0}
    for w in WORKERS:
        if w["status"] == "former":
            continue
        summary["active"] += 1
        if w["status"] == "ok":
            summary["ok"] += 1
        if w["status"] == "blocked":
            summary["lapsed"] += 1
        if w["pending"]:
            summary["pending"] += 1
        for d in w["creds"].values():
            if d and 0 <= (d - TODAY).days <= 30:
                summary["soon"] += 1
                break
    return summary


def get_worker(slug):
    for w in WORKERS:
        if w["slug"] != slug:
            continue
        w = dict(w)
        history = []
        for key, exp in w["creds"].items():
            if exp:
                # first aid lasts 1 year, the others 3 years
                years = 1 if key == "firstaid" else 3
                uploaded = date(exp.year - years, exp.month, min(exp.day, 28))
                history.append({"doc": CRED_NAME[key], "version": "v2", "by": "S. Chen",
                                "on": uploaded, "expiry": exp})
        history.sort(key=lambda h: h["on"], reverse=True)
        w["history"] = history
        w["training"] = TRAINING
        return w
    return None


# ---- Participants ----
PARTICIPANTS = [
    {"id": "P-1042", "name": "Jordan Tallis", "support": "Supported independent living", "location": "SIL, 14 Kembla St",
     "key_worker": "Marcus Webb", "team": ["Marcus Webb", "Priya Nair"], "plan": "current",
     "plan_reviewed": date(2026, 3, 14), "plan_next": date(2027, 3, 14), "restrictive": False,
     "care": ["Full physical assistance with transfers and personal care.",
              "Non-verbal. Communicates with an AAC device and key word sign.",
              "Medication administered twice daily from a Webster pack.",
              "Becomes distressed in loud environments. Plan community access for quiet times."],
     "care_history": [(date(2026, 9, 14), "Sarah Chen", "Communication guidance updated after speech pathology review.")],
     "consent": [("Collect and store personal information", "given", date(2026, 3, 14), "Jordan, with support from nominee"),
                 ("Share with family: Leanne Tallis (mother)", "given", date(2026, 3, 14), "Jordan"),
                 ("Share with GP: Dr A. Russo", "given", date(2026, 3, 14), "Jordan"),
                 ("Share with other providers", "withdrawn", date(2026, 8, 2), "Leanne Tallis (nominee)")],
     "plans": [("Core support plan", "current", date(2026, 3, 14), date(2027, 3, 14)),
               ("Medication management plan", "current", date(2026, 6, 11), date(2027, 6, 11))],
     "risks": ["RSK-2026-0091"], "agreement": date(2026, 3, 10)},
    {"id": "P-1088", "name": "Ana Mercado", "support": "Supported independent living", "location": "SIL, 14 Kembla St",
     "key_worker": "Sarah Chen", "team": ["Sarah Chen", "Ethan Brooks"], "plan": "due",
     "plan_reviewed": date(2025, 10, 2), "plan_next": date(2026, 10, 2), "restrictive": True,
     "care": ["Behaviour support plan in place. Follow de-escalation steps in section 4.",
              "Authorised restrictive practice: locked kitchen cupboard (environmental). Record each use.",
              "Prefers female support workers for personal care."],
     "care_history": [(date(2026, 7, 20), "Sarah Chen", "Restrictive practice authorisation renewed until July 2027.")],
     "consent": [("Collect and store personal information", "given", date(2025, 10, 2), "Public guardian"),
                 ("Share with family", "not_asked", None, None),
                 ("Share with GP: Dr L. Huang", "given", date(2025, 10, 2), "Public guardian"),
                 ("Share with behaviour support practitioner", "given", date(2025, 10, 2), "Public guardian")],
     "plans": [("Core support plan", "due", date(2025, 10, 2), date(2026, 10, 2)),
               ("Behaviour support plan", "due", date(2025, 10, 2), date(2026, 10, 2))],
     "risks": ["RSK-2026-0114", "RSK-2026-0064"], "agreement": date(2025, 9, 28)},
    {"id": "P-1103", "name": "Rhys Whitlock", "support": "Community participation", "location": "Community access",
     "key_worker": "Marcus Webb", "team": ["Marcus Webb", "Liam Petersen"], "plan": "current",
     "plan_reviewed": date(2026, 7, 8), "plan_next": date(2027, 7, 8), "restrictive": False,
     "care": ["Independent with personal care. Needs prompting with money handling.",
              "Epilepsy management plan applies. Seizure response steps are attached.",
              "Uses public transport with a support worker."],
     "care_history": [],
     "consent": [("Collect and store personal information", "given", date(2026, 7, 8), "Rhys"),
                 ("Share with family: Paul Whitlock (brother)", "given", date(2026, 7, 8), "Rhys"),
                 ("Share with GP", "given", date(2026, 7, 8), "Rhys")],
     "plans": [("Core support plan", "current", date(2026, 7, 8), date(2027, 7, 8))],
     "risks": ["RSK-2026-0087"], "agreement": date(2026, 7, 1)},
    {"id": "P-1119", "name": "Thi Ngo", "support": "Therapy supports", "location": "In home",
     "key_worker": "Priya Nair", "team": ["Priya Nair"], "plan": "due",
     "plan_reviewed": date(2025, 10, 9), "plan_next": date(2026, 10, 9), "restrictive": False,
     "care": ["Home exercise program three times a week, led by the physiotherapist's plan.",
              "Hearing impaired. Face Thi when speaking and confirm understanding."],
     "care_history": [],
     "consent": [("Collect and store personal information", "given", date(2025, 10, 9), "Thi"),
                 ("Share with physiotherapist", "given", date(2025, 10, 9), "Thi")],
     "plans": [("Therapy support plan", "due", date(2025, 10, 9), date(2026, 10, 9))],
     "risks": [], "agreement": date(2025, 10, 1)},
    {"id": "P-1130", "name": "Margot Delacroix", "support": "Supported independent living", "location": "SIL, 2 Boronia Ave",
     "key_worker": "Priya Nair", "team": ["Priya Nair", "Ruby Nguyen"], "plan": "not_started",
     "plan_reviewed": None, "plan_next": date(2026, 10, 19), "restrictive": False,
     "care": ["Intake in progress. Interim care notes from the hospital discharge summary apply."],
     "care_history": [],
     "consent": [],
     "plans": [("Core support plan", "not_started", None, date(2026, 10, 19))],
     "risks": [], "agreement": None},
]
for _p in PARTICIPANTS:
    _p["slug"] = _p["id"].lower()
    _p["first"] = _p["name"].split()[0]
    _p["short"] = _p["name"].split()[0][0] + ". " + _p["name"].split()[-1]

NOTES = [
    {"date": date(2026, 9, 26), "pid": "P-1042", "type": "progress", "by": "Marcus Webb", "status": "submitted",
     "text": "Morning routine went well. Jordan chose to go to the library and stayed 40 minutes.", "follow_up": False, "incident": False},
    {"date": date(2026, 9, 26), "pid": "P-1042", "type": "handover", "by": "Marcus Webb", "to": "Priya Nair", "status": "submitted",
     "text": "Webster pack for next week not yet delivered. Pharmacy said Monday.", "follow_up": True, "incident": False},
    {"date": date(2026, 9, 26), "pid": "P-1042", "type": "progress", "by": "Marcus Webb", "status": "submitted",
     "text": "Jordan fell during a hoist transfer at 2:10 pm. Ambulance called; wrist x-ray at hospital. Hoist sling looks worn.", "follow_up": False, "incident": True},
    {"date": date(2026, 9, 25), "pid": "P-1088", "type": "progress", "by": "Sarah Chen", "status": "submitted",
     "text": "Calm day. Kitchen cupboard lock used once at 6:10 pm and recorded.", "follow_up": False, "incident": False},
    {"date": date(2026, 9, 25), "pid": "P-1088", "type": "handover", "by": "Ethan Brooks", "to": "Sarah Chen", "status": "submitted",
     "text": "Ana asked twice about her sister's visit. Please confirm the date with the guardian.", "follow_up": True, "incident": False},
    {"date": date(2026, 9, 24), "pid": "P-1103", "type": "progress", "by": "Marcus Webb", "status": "draft",
     "text": "Bus trip to the markets. Rhys managed his own purchases with one prompt.", "follow_up": False, "incident": False},
    {"date": date(2026, 9, 23), "pid": "P-1119", "type": "progress", "by": "Priya Nair", "status": "submitted",
     "text": "Completed full exercise set. Reported knee soreness afterwards.", "follow_up": True, "incident": False},
    {"date": date(2026, 9, 19), "pid": "P-1130", "type": "progress", "by": "Priya Nair", "status": "submitted",
     "text": "First day at Boronia Ave. Settled well and ate dinner with housemates.", "follow_up": False, "incident": False},
]


def participants_for(role):
    # staff only see the participants they support
    if role == "staff":
        me = ROLES["staff"]["user"]
        return [p for p in PARTICIPANTS if me in p["team"]]
    return PARTICIPANTS


def notes_for(role):
    visible = []
    names = {}
    for p in participants_for(role):
        visible.append(p["id"])
    for p in PARTICIPANTS:
        names[p["id"]] = p["name"]
    result = []
    for n in NOTES:
        if n["pid"] in visible:
            note = dict(n)
            note["participant"] = names[n["pid"]]
            note["pslug"] = n["pid"].lower()
            result.append(note)
    return result


def participant_summary(role):
    summary = {"active": 0, "current": 0, "due": 0, "restrictive": 0, "follow_up": 0}
    for p in participants_for(role):
        summary["active"] += 1
        if p["plan"] == "current":
            summary["current"] += 1
        if p["plan"] == "due" or p["plan"] == "not_started":
            summary["due"] += 1
        if p["restrictive"]:
            summary["restrictive"] += 1
    for n in notes_for(role):
        if n["follow_up"]:
            summary["follow_up"] += 1
    return summary


def get_participant(slug, role):
    for p in participants_for(role):
        if p["slug"] != slug:
            continue
        p = dict(p)
        p["risk_rows"] = []
        for ref in p["risks"]:
            for r in risks_with_status():
                if r["ref"] == ref:
                    p["risk_rows"].append(r)
        p["notes"] = []
        for n in notes_for(role):
            if n["pid"] == p["id"]:
                p["notes"].append(n)
        return p
    return None



# ---- Incidents & complaints ----
STAGES = ["Reported", "Under review", "Investigation", "Action required", "Resolved", "Closed"]
CATEGORIES_INC = ["Death of a participant", "Serious injury", "Abuse or neglect",
                  "Unlawful sexual or physical contact or assault", "Sexual misconduct", "Unauthorised restrictive practice",
                  "Medication error", "Near miss", "Property damage", "Service quality (complaint)", "Communication (complaint)"]

_C = lambda **k: k
CASES = [
    _C(ref="INC-2026-0044", type="Incident", date=date(2026, 9, 26), time="2:18 pm", pid="P-1042", category="Serious injury",
       reportable="yes", stage=1, commission_ref=None, notified=None, owner="Sarah Chen", reporter="Marcus Webb",
       location="SIL, 14 Kembla St", severity="High",
       what="Jordan fell during a hoist transfer from wheelchair to bed. The sling strap slipped on one side.",
       response="First aid given, ambulance called at 2:15 pm. Jordan taken to Redland Hospital for a wrist x-ray. Hoist taken out of use.",
       emergency="Yes", injury="Yes, suspected wrist fracture", witnesses="Priya Nair (Team Leader)",
       risk="RSK-2026-0091", actions=[("Inspect and replace hoist slings at Kembla St", "Douglas Okafor", date(2026, 9, 30), "open")],
       history=[(date(2026, 9, 26), "2:18 pm", "Marcus Webb", "Reported from a progress note"),
                (date(2026, 9, 26), "3:05 pm", "Sarah Chen", "Marked reportable, 24-hour notification started"),
                (date(2026, 9, 26), "3:07 pm", "Sarah Chen", "Moved to Under review")]),
    _C(ref="INC-2026-0043", type="Incident", date=date(2026, 9, 24), time="7:40 pm", pid="P-1088", category="Abuse or neglect",
       reportable="yes", stage=3, commission_ref="NDIS-2026-88431", notified=date(2026, 9, 25), owner="Sarah Chen", reporter="Ethan Brooks",
       location="SIL, 14 Kembla St", severity="High",
       what="Ana's evening meal and medication were missed when a shift was left uncovered for two hours.",
       response="Ana checked and settled. Medication given late after GP advice by phone.",
       emergency="No", injury="No", witnesses="—", risk="RSK-2026-0102",
       actions=[("Review rostering escalation for uncovered shifts", "Douglas Okafor", date(2026, 9, 20), "verified"),
                ("Brief all Kembla St staff on the missed-shift procedure", "Sarah Chen", date(2026, 9, 25), "open")],
       history=[(date(2026, 9, 24), "8:02 pm", "Ethan Brooks", "Reported"),
                (date(2026, 9, 24), "8:30 pm", "Sarah Chen", "Marked reportable"),
                (date(2026, 9, 25), "9:12 am", "Douglas Okafor", "Commission reference NDIS-2026-88431 recorded"),
                (date(2026, 9, 25), "11:00 am", "Sarah Chen", "Moved to Action required")]),
    _C(ref="INC-2026-0042", type="Incident", date=date(2026, 9, 21), time="11:15 am", pid="P-1103", category="Unauthorised restrictive practice",
       reportable="yes", stage=2, commission_ref="NDIS-2026-88190", notified=date(2026, 9, 21), owner="Sarah Chen", reporter="Liam Petersen",
       location="Community access, Cleveland markets", severity="Medium",
       what="A worker held Rhys's wrist to stop him crossing the road. Not part of an authorised behaviour support plan.",
       response="Rhys was unhurt. Debrief with the worker the same day.", emergency="No", injury="No", witnesses="Member of the public",
       risk="RSK-2026-0064", actions=[("Interview worker and complete investigation report", "Sarah Chen", date(2026, 10, 5), "open")],
       history=[(date(2026, 9, 21), "12:00 pm", "Liam Petersen", "Reported"),
                (date(2026, 9, 21), "1:30 pm", "Douglas Okafor", "Commission reference NDIS-2026-88190 recorded"),
                (date(2026, 9, 22), "9:00 am", "Sarah Chen", "Moved to Investigation")]),
    _C(ref="INC-2026-0041", type="Incident", date=date(2026, 9, 18), time="8:05 am", pid="P-1119", category="Medication error",
       reportable="no", no_reason="Missed vitamin supplement. No harm and no risk of harm. Not a reportable incident.",
       stage=1, commission_ref=None, notified=None, owner="Priya Nair", reporter="Priya Nair",
       location="In home", severity="Low", what="Morning vitamin D supplement not given.", response="Given at lunch after checking with the pharmacist.",
       emergency="No", injury="No", witnesses="—", risk="RSK-2026-0102",
       actions=[("Add supplement to the medication chart checklist", "Priya Nair", date(2026, 9, 24), "open")],
       history=[(date(2026, 9, 18), "9:00 am", "Priya Nair", "Reported"), (date(2026, 9, 18), "2:00 pm", "Sarah Chen", "Marked not reportable")]),
    _C(ref="INC-2026-0040", type="Incident", date=date(2026, 9, 12), time="4:30 pm", pid="P-1130", category="Near miss",
       reportable="pending", stage=0, commission_ref=None, notified=None, owner=None, reporter="Marcus Webb",
       location="SIL, 2 Boronia Ave", severity="Low", what="Hot water at the bathroom tap measured above the safe limit before a shower.",
       response="Shower not used. Maintenance contacted.", emergency="No", injury="No", witnesses="—", risk=None, actions=[],
       history=[(date(2026, 9, 12), "4:45 pm", "Marcus Webb", "Reported")]),
    _C(ref="CAS-2026-0045", type="Complaint", date=date(2026, 9, 23), time="10:00 am", pid="P-1103", category="Service quality (complaint)",
       reportable="no", no_reason="Complaint about service timeliness. Not a reportable incident.", stage=1, commission_ref=None, notified=None,
       owner="Sarah Chen", reporter="Sarah Chen", location="Phone call from family", severity="Low",
       what="Paul Whitlock says workers have arrived 20 to 30 minutes late three times this month.",
       response="Apology given. Rostering asked to review travel times.", emergency="No", injury="No", witnesses="—", risk=None,
       actions=[("Call Paul Whitlock with the outcome", "Sarah Chen", date(2026, 10, 7), "open")],
       history=[(date(2026, 9, 23), "10:15 am", "Sarah Chen", "Complaint recorded")]),
    _C(ref="INC-2026-0039", type="Incident", date=date(2026, 9, 4), time="6:20 pm", pid="P-1042", category="Serious injury",
       reportable="yes", stage=5, commission_ref="NDIS-2026-87344", notified=date(2026, 9, 4), owner="Sarah Chen", reporter="Priya Nair",
       location="SIL, 14 Kembla St", severity="High", what="Burn to forearm from a kettle.", response="First aid, GP review next day.",
       emergency="No", injury="Yes, minor burn", witnesses="—", risk=None,
       actions=[("Install kettle tipper", "Douglas Okafor", date(2026, 9, 10), "verified")],
       history=[(date(2026, 9, 4), "6:40 pm", "Priya Nair", "Reported"), (date(2026, 9, 18), "3:00 pm", "Sarah Chen", "Closed")]),
    _C(ref="CAS-2026-0038", type="Complaint", date=date(2026, 7, 28), time="1:00 pm", pid="P-1088", category="Service quality (complaint)",
       reportable="no", no_reason="Not reportable.", stage=5, commission_ref=None, notified=None, owner="Priya Nair", reporter="Priya Nair",
       location="Email from guardian", severity="Low", what="Guardian unhappy with the cleanliness of the shared kitchen.", response="Deep clean booked.",
       emergency="No", injury="No", witnesses="—", risk=None, actions=[("Weekly cleaning checklist added", "Priya Nair", date(2026, 8, 5), "verified")],
       history=[(date(2026, 7, 28), "1:00 pm", "Priya Nair", "Complaint recorded"), (date(2026, 8, 12), "10:00 am", "Sarah Chen", "Closed")]),
    _C(ref="INC-2026-0037", type="Incident", date=date(2026, 6, 19), time="3:00 pm", pid="P-1103", category="Property damage",
       reportable="no", no_reason="Not reportable.", stage=5, commission_ref=None, notified=None, owner="Sarah Chen", reporter="Marcus Webb",
       location="Community access", severity="Low", what="Rhys's phone screen cracked on the bus.", response="Family informed.",
       emergency="No", injury="No", witnesses="—", risk=None, actions=[],
       history=[(date(2026, 6, 19), "3:30 pm", "Marcus Webb", "Reported"), (date(2026, 6, 25), "9:00 am", "Sarah Chen", "Closed")]),
]


def _case(c):
    case = dict(c)
    case["slug"] = c["ref"].lower()
    case["participant"] = c["pid"]
    for p in PARTICIPANTS:
        if p["id"] == c["pid"]:
            case["participant"] = p["name"]
    case["stage_name"] = STAGES[c["stage"]]
    case["closed"] = c["stage"] == 5
    case["no_reason"] = c.get("no_reason")

    case["action_rows"] = []
    case["open_actions"] = 0
    case["overdue_actions"] = 0
    for text, owner, due, status in c["actions"]:
        overdue = status == "open" and due < TODAY
        case["action_rows"].append({"text": text, "owner": owner, "due": due,
                                    "status": status, "overdue": overdue})
        if status != "verified":
            case["open_actions"] += 1
        if overdue:
            case["overdue_actions"] += 1
    return case


def cases_for(role):
    rows = []
    for c in CASES:
        case = _case(c)
        if role == "staff" and case["reporter"] != ROLES["staff"]["user"]:
            continue
        rows.append(case)
    # cases with overdue actions first
    rows.sort(key=lambda c: c["overdue_actions"] == 0)
    return rows


def get_case(slug):
    for c in CASES:
        if c["ref"].lower() == slug:
            return _case(c)
    return None


def case_summary():
    summary = {"open": 0, "awaiting_ref": 0, "overdue": 0, "closed_quarter": 0}
    for c in CASES:
        case = _case(c)
        if case["closed"]:
            if case["date"] >= date(2026, 7, 1):
                summary["closed_quarter"] += 1
            continue
        summary["open"] += 1
        summary["overdue"] += case["overdue_actions"]
        if case["reportable"] == "yes" and not case["commission_ref"]:
            summary["awaiting_ref"] += 1
    return summary


# ---- My compliance ----
READS = [  # title, version, published, slug
    ("Code of Conduct Policy", "4.0", date(2026, 3, 12), "code-of-conduct-policy"),
    ("Incident Management Policy", "3.1", date(2026, 8, 24), "incident-management-policy"),
    ("Work Health and Safety Policy", "1.3", date(2026, 2, 2), "work-health-and-safety-policy"),
    ("Violence, Abuse, Neglect & Discrimination-Free Policy", "3.0", date(2026, 1, 22), "violence-abuse-neglect-discrimination-free-policy"),
]
READ_DUE = {"Code of Conduct Policy": date(2026, 10, 10), "Incident Management Policy": date(2026, 10, 14),
            "Work Health and Safety Policy": date(2026, 3, 15),
            "Violence, Abuse, Neglect & Discrimination-Free Policy": date(2026, 10, 15)}
ACKNOWLEDGED = {"Marcus Webb": {"Work Health and Safety Policy", "Violence, Abuse, Neglect & Discrimination-Free Policy"},
                "Sarah Chen": {"Code of Conduct Policy", "Incident Management Policy", "Work Health and Safety Policy"},
                "Douglas Okafor": {"Incident Management Policy", "Work Health and Safety Policy",
                                   "Violence, Abuse, Neglect & Discrimination-Free Policy"}}
EXTRA_TODOS = {
    "Marcus Webb": [
        {"kind": "action", "title": "Complete the manual handling refresher", "from": "Internal audit finding", "due": date(2026, 9, 25)},
        {"kind": "note", "title": "Finish your progress note for Rhys Whitlock", "from": "Draft from 24 Sep", "due": date(2026, 9, 28),
         "link": ("participants", None)},
    ],
}


def my_compliance(role):
    return my_compliance_for(ROLES[role]["user"])


def my_compliance_for(me):
    w = get_worker(_slug(me))
    todos = []

    # corrective actions from open cases
    for c in CASES:
        if c["stage"] == 5:
            continue
        for text, owner, due, status in c["actions"]:
            if owner == me and status == "open":
                todos.append({"kind": "action", "title": text, "from": c["ref"],
                              "due": due, "case": c["ref"].lower()})

    # policies to read
    acked = ACKNOWLEDGED.get(me, set())
    reads = []
    for title, ver, pub, slug in READS:
        done = title in acked
        reads.append({"title": title, "version": ver, "published": pub, "slug": slug, "done": done})
        if not done:
            todos.append({"kind": "read", "title": f"Read and acknowledge {title} v{ver}",
                          "doc": title, "version": ver,
                          "from": "Published " + fmt_date(pub), "due": READ_DUE[title]})

    for t in EXTRA_TODOS.get(me, []):
        todos.append(dict(t))
    for t in todos:
        t["overdue"] = t["due"] < TODAY
    todos.sort(key=lambda t: (not t["overdue"], t["due"]))

    mine = []
    for p in PARTICIPANTS:
        if me in p["team"]:
            mine.append(p)

    manager = None
    if w["name"] != "Douglas Okafor":
        for x in WORKERS:
            if x["name"] == w["manager"]:
                manager = x

    # first certificate expiring in the next 30 days (not already renewed)
    expiring = None
    for key, d in w["creds"].items():
        if w["pending"] and w["pending"]["key"] == key:
            continue
        if d and 0 <= (d - TODAY).days <= 30 and expiring is None:
            expiring = {"key": key, "date": d, "days": (d - TODAY).days}

    counts = {"current": 0, "soon": 0, "bad": 0}
    for state in w["cred_state"].values():
        if state == "ok":
            counts["current"] += 1
        else:
            counts[state] += 1

    return {"me": w, "todos": todos, "reads": reads, "participants": mine, "manager": manager,
            "expiring": expiring, "counts": counts}


def personal_alert(role):
    # line on the dashboard when the admin/manager's own record needs something
    if role == "staff":
        return None
    mc = my_compliance(role)
    w = mc["me"]

    soonest = None
    for key, d in w["creds"].items():
        if w["pending"] and w["pending"]["key"] == key:
            continue
        if d and (d - TODAY).days <= 30:
            if soonest is None or d < soonest[1]:
                soonest = (key, d)
    if soonest:
        key, d = soonest
        days = (d - TODAY).days
        if days < 0:
            return {"title": f"Your {CRED_NAME[key]} has lapsed", "body": "Upload a current certificate."}
        return {"title": f"Your {CRED_NAME[key]} expires in {days} days",
                "body": f"Upload the renewal before {fmt_date(d)}."}

    n = len(mc["todos"])
    if n == 0:
        return None
    late = 0
    for t in mc["todos"]:
        if t["overdue"]:
            late += 1
    title = f"You have {n} item to do" if n == 1 else f"You have {n} items to do"
    body = f"{late} overdue." if late else "Nothing overdue."
    return {"title": title, "body": body}


# ---- Organisation setup ----
REG_GROUPS = [
    # code, name, cert or ver, module
    ("0107", "Assistance with daily personal activities", "cert", None),
    ("0104", "High intensity daily personal activities", "cert", "M1"),
    ("0110", "Specialist positive behaviour support", "cert", "M2"),
    ("0132", "Specialised support coordination", "cert", "M4"),
    ("0136", "Group and centre-based activities", "cert", None),
    ("0138", "Assistance with supported independent living", "cert", "M5A"),
    ("0102", "Assistance to access and maintain employment or higher education", "cert", None),
    ("0106", "Assistance in coordinating or managing life stages, transitions and supports", "cert", None),
    ("0115", "Assistance with daily life tasks in a group or shared living arrangement", "cert", None),
    ("0117", "Development of daily living and life skills", "cert", None),
    ("0118", "Early intervention supports for early childhood", "cert", "M3"),
    ("0125", "Participation in community, social and civic activities", "cert", None),
    ("0131", "Specialist disability accommodation", "cert", "M5"),
    ("0133", "Specialised supported employment", "cert", None),
    ("0137", "Providing an NDIS digital platform service", "cert", None),
    ("0101", "Accommodation / tenancy assistance", "ver", None),
    ("0103", "Assistive products for personal care and safety", "ver", None),
    ("0105", "Personal mobility equipment", "ver", None),
    ("0108", "Assistance with travel / transport arrangements", "ver", None),
    ("0109", "Vehicle modifications", "ver", None),
    ("0111", "Home modifications", "ver", None),
    ("0112", "Assistive equipment for recreation", "ver", None),
    ("0113", "Vision equipment", "ver", None),
    ("0114", "Community nursing care", "ver", None),
    ("0116", "Innovative community participation", "ver", None),
    ("0119", "Specialised hearing services", "ver", None),
    ("0120", "Household tasks", "ver", None),
    ("0121", "Interpreting and translation", "ver", None),
    ("0122", "Hearing equipment", "ver", None),
    ("0123", "Assistive products for household tasks", "ver", None),
    ("0124", "Communication and information equipment", "ver", None),
    ("0126", "Exercise physiology and personal training", "ver", None),
    ("0127", "Management of funding for supports in participant plans", "ver", None),
    ("0128", "Therapeutic supports", "ver", None),
    ("0129", "Specialised driver training", "ver", None),
    ("0130", "Assistance animals", "ver", None),
    ("0134", "Hearing services", "ver", None),
    ("0135", "Customised prosthetics", "ver", None),
]
CORE_BASELINE = 43
CONDITIONAL_ITEMS = 7
CONDITIONAL_CODES = ["0104", "0107", "0110", "0118"]
VERIFICATION_BASELINE = 9


def module_counts():
    out = {}
    for r in MODULE_REQUIREMENTS:
        out[r["module"]] = out.get(r["module"], 0) + 1
    return out


def requirement_total(groups=None):
    if groups is None:
        groups = SELECTED_GROUPS
    cert = False
    for code, name, pathway, module in REG_GROUPS:
        if code in groups and pathway == "cert":
            cert = True
    if not cert:
        return {"pathway": "Verification", "baseline": VERIFICATION_BASELINE,
                "modules": 0, "total": VERIFICATION_BASELINE}

    base = CORE_BASELINE
    for code in CONDITIONAL_CODES:
        if code in groups:
            base += CONDITIONAL_ITEMS
            break
    modules = len(missing_documents(groups))
    return {"pathway": "Certification", "baseline": base, "modules": modules, "total": base + modules}


SETUP_STEPS = [
    ("profile", "Organisation profile", "Legal identity"),
    ("insurance", "Corporate insurance", "Public liability"),
    ("groups", "Registration groups", "Scope of service"),
    ("people", "Key personnel", "Screening and roles"),
    ("rules", "Operating rules", "Sign-off rules"),
]
SETUP_DONE = 3

ORG_PROFILE = {
    "legal": "Brightwater Support Services Pty Ltd", "trading": "Brightwater Care",
    "abn": "41 892 553 107", "ndis": "4050 087 312", "type": "Company (body corporate)",
    "state": "Queensland", "contact": "Douglas Okafor", "email": "d.okafor@brightwatercare.com.au",
    "phone": "07 3821 4470",
}
ORG_TYPES = ["Sole trader", "Partnership", "Company (body corporate)", "Trust", "Incorporated association"]
STATES = ["Queensland", "New South Wales", "Victoria", "South Australia", "Western Australia",
          "Tasmania", "Northern Territory", "Australian Capital Territory"]

INSURANCE = [
    {"type": "Public liability", "insurer": "CGU Insurance", "policy": "PL-2026-88134", "cover": "$10,000,000",
     "expires": date(2026, 10, 23), "file": "CGU-public-liability-2025-26.pdf"},
    {"type": "Professional indemnity", "insurer": "QBE Insurance", "policy": "PI-2025-40217", "cover": "$5,000,000",
     "expires": date(2026, 11, 24), "file": "QBE-professional-indemnity-2025-26.pdf"},
]
INSURANCE_TYPES = ["Public liability", "Professional indemnity", "Workers compensation", "Other"]

KEY_PERSONNEL = ["Douglas Okafor", "Sarah Chen", "Priya Nair"]


def key_personnel():
    people = []
    for name in KEY_PERSONNEL:
        w = get_worker(_slug(name))
        if w["login"] in ROLES:
            role = ROLES[w["login"]]["label"]
        else:
            role = "Staff Member"
        people.append({"name": name, "slug": w["slug"], "position": w["position"],
                       "initials": w["initials"], "role": role,
                       "invited": w["login"] == "invited", "screening": w["creds"]["screening"]})
    return people
