"""Provisional MVP fields. No legal checklist or risk matrix is inferred."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    label: str
    kind: str = "text"
    required: bool = False
    limit: int = 10000
    choices: tuple = ()


def text(label, required=False, limit=250):
    return Field(label, required=required, limit=limit)


def date(label):
    return Field(label, "date")


def choice(label, values, required=False):
    return Field(label, "choice", required, choices=tuple(values.split()))


COMMON = {"source_reference": text("Legacy reference", limit=150)}
DEFINITIONS = {
    "staff": {**COMMON,
        "first_name": text("First name", True, 120), "last_name": text("Last name", True, 120),
        "email": Field("Email", "email", limit=255), "phone": text("Phone", limit=50),
        "job_title": text("Job title (does not grant a login or role)", limit=120),
        "start_date": date("Start date"), "employment_type": text("Employment type", limit=80),
        "is_active": choice("Active", "yes no"),
    },
    "participant": {**COMMON,
        "first_name": text("First name", True, 120), "last_name": text("Last name", True, 120),
        "date_of_birth": date("Date of birth"), "ndis_number": text("NDIS number", limit=50),
        "support_type": text("Support type", limit=150), "plan_status": text("Plan status", limit=50),
        "plan_start_date": date("Plan start"), "plan_end_date": date("Plan end"),
        "key_worker_reference": text("Key worker legacy staff reference", limit=150),
        "care_requirements": Field("Care requirements"),
        "emergency_contact_name": text("Emergency contact", limit=200),
        "emergency_contact_phone": text("Emergency phone", limit=50),
    },
    "credential": {**COMMON,
        "staff_reference": text("Legacy staff reference", True, 150),
        "credential_type": text("Credential type (configured catalogue)", True, 150),
        "issue_date": date("Issue date"), "expiry_date": date("Expiry date"),
    },
    "incident": {**COMMON,
        "category": text("Category", True, 80), "description": Field("Description", required=True),
        "occurred_at": Field("Event time with UTC offset", "datetime", True),
        "reported_at": Field("Provider awareness / reported time with UTC offset", "datetime", True),
        "severity": choice("Severity", "low medium high critical", True),
        "status": choice("Historical status", "reported reviewed assigned investigating corrective_action resolved closed", True),
        "reportability": choice("Reportability decision for reviewer confirmation", "requires_review yes no", True),
        "location": text("Location"), "immediate_response": Field("Immediate response"),
        "investigation_notes": Field("Investigation notes"), "outcome": Field("Outcome"),
        "closed_at": Field("Historical closure time with UTC offset", "datetime"),
        "reporter_reference": text("Legacy reporting staff reference", limit=150),
        "participant_reference": text("Legacy participant reference", limit=150),
    },
    "complaint": {},
    "risk": {**COMMON,
        "title": text("Title", True), "description": Field("Description"),
        "category": text("Category", limit=100),
        "likelihood": Field("Likelihood (1–5)", "score"), "consequence": Field("Consequence (1–5)", "score"),
        "rating": choice("Source risk rating (not recalculated)", "low medium high critical"),
        "residual_rating": choice("Source residual rating", "low medium high critical"),
        "status": choice("Status", "open assessed treating monitoring closed", True),
        "existing_controls": Field("Existing controls"), "treatment": Field("Treatment"),
        "review_date": date("Review date"), "owner_reference": text("Legacy owner staff reference", limit=150),
    },
}
DEFINITIONS["complaint"] = dict(DEFINITIONS["incident"])
LABELS = {"staff": "Staff", "participant": "Participants", "credential": "Staff credentials",
          "incident": "Historical incidents", "complaint": "Historical complaints", "risk": "Risks"}
DATE_FORMATS = {"iso": "%Y-%m-%d", "dmy": "%d/%m/%Y", "mdy": "%m/%d/%Y"}
