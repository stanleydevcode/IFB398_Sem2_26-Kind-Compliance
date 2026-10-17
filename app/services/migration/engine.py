"""Shared validation and transactional writes to the real domain models.

Call these inside tenant_session(), after authorising the current membership.
Imports never create users, calculate legal deadlines, or send notifications.
"""
import hashlib
import json
import re
from datetime import date, datetime, timezone

from sqlalchemy import func, select, text

from app.models import Staff, StaffCredential, Participant, Case, Risk, CredentialType, AuditLog
from app.models.base import utcnow
from app.models.migration import MigrationJob, MigrationRow, SourceIdentity, MigrationChange
from app.services.migration.definitions import DEFINITIONS, DATE_FORMATS
from app.services.migration.reader import MigrationError

MODELS = {"staff": Staff, "participant": Participant, "credential": StaffCredential,
          "incident": Case, "complaint": Case, "risk": Risk}
RELATIONS = {"staff_reference": ("staff", "staff_id"),
             "key_worker_reference": ("staff", "key_worker_staff_id"),
             "reporter_reference": ("staff", "reported_by_staff_id"),
             "participant_reference": ("participant", "participant_id"),
             "owner_reference": ("staff", "owner_staff_id")}
FINAL = {"imported", "skipped"}
DATE_RANGES = (("issue_date", "expiry_date"), ("plan_start_date", "plan_end_date"),
               ("occurred_at", "reported_at"), ("occurred_at", "closed_at"))


def lock_imports(session, organisation_id):
    """Serialize migration writes across jobs in this organisation on PostgreSQL."""
    if session.bind.dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(("migration:" + organisation_id).encode()).digest()[:8],
                             "big", signed=True)
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})


def audit(session, actor, action, entity_type, entity_id, changes=None):
    session.add(AuditLog(user_id=actor, action=action, entity_type=entity_type,
                         entity_id=entity_id, changes=changes or {}))


def snapshot(record):
    return {c.name: (getattr(record, c.name).isoformat()
                    if isinstance(getattr(record, c.name), (date, datetime)) else getattr(record, c.name))
            for c in record.__table__.columns}


def fingerprint(record):
    return hashlib.sha256(json.dumps(snapshot(record), sort_keys=True, default=str).encode()).hexdigest()


def date_range_errors(values):
    """Check incoming or merged dates without modifying the stored record.

    Normalisation handles malformed fields. Datetimes are compared in UTC;
    SQLite returns stored UTC timestamps without their timezone information.
    """
    errors = []
    for start, end in DATE_RANGES:
        if not values.get(start) or not values.get(end):
            continue
        try:
            if start.endswith("_at"):
                endpoints = []
                for key in (start, end):
                    value = values[key]
                    value = value if isinstance(value, datetime) else datetime.fromisoformat(value)
                    endpoints.append(value.replace(tzinfo=timezone.utc) if value.tzinfo is None
                                     else value.astimezone(timezone.utc))
            else:
                endpoints = [value if isinstance(value, date) else date.fromisoformat(value)
                             for value in (values[start], values[end])]
        except (TypeError, ValueError):
            continue  # Field-format errors are already reported by normalise().
        if endpoints[1] < endpoints[0]:
            errors.append(f"{end} cannot precede {start}.")
    return errors


def source_target(session, system, kind, reference):
    identity = session.scalar(select(SourceIdentity).filter_by(
        source_system=system, entity_type=kind, source_reference=reference))
    if identity:
        return session.get(MODELS[kind], identity.destination_id)
    return None


def label(record):
    if isinstance(record, (Staff, Participant)):
        return f"{record.first_name} {record.last_name}"
    if isinstance(record, Risk):
        return record.title
    if isinstance(record, Case):
        return record.reference or record.id
    return f"Credential {record.id}"


def candidates_for(session, job, data):
    matches = {}
    if data.get("source_reference"):
        target = source_target(session, job.source_system, job.record_type, data["source_reference"])
        if target:
            matches[target.id] = target
    query = None
    kind = job.record_type
    if kind == "staff":
        clauses = [func.lower(Staff.first_name) == data.get("first_name", "").lower(),
                   func.lower(Staff.last_name) == data.get("last_name", "").lower()]
        query = select(Staff).where(*clauses)
        if data.get("email"):
            query = select(Staff).where((func.lower(Staff.email) == data["email"]) |
                                       (clauses[0] & clauses[1]))
    elif kind == "participant":
        clauses = [func.lower(Participant.first_name) == data.get("first_name", "").lower(),
                   func.lower(Participant.last_name) == data.get("last_name", "").lower()]
        query = select(Participant).where(*clauses)
        if data.get("ndis_number"):
            query = select(Participant).where((Participant.ndis_number == data["ndis_number"]) |
                                              (clauses[0] & clauses[1]))
    elif kind == "risk" and data.get("title"):
        query = select(Risk).where(func.lower(Risk.title) == data["title"].lower())
    elif kind in {"incident", "complaint"} and data.get("description"):
        query = select(Case).where(Case.case_type == kind, Case.description == data["description"])
    elif kind == "credential":
        staff = source_target(session, job.source_system, "staff", data.get("staff_reference", ""))
        ctype = session.scalar(select(CredentialType).where(
            func.lower(CredentialType.name) == data.get("credential_type", "").lower()))
        if staff and ctype:
            query = select(StaffCredential).where(StaffCredential.staff_id == staff.id,
                                                  StaffCredential.credential_type_id == ctype.id)
    if query is not None:
        for record in session.scalars(query):
            matches[record.id] = record
    return list(matches.values())


def normalise(job, supplied):
    data, errors, warnings = {}, [], []
    for key, field in DEFINITIONS[job.record_type].items():
        value = str(supplied.get(key, "") or "").strip()
        if field.required and not value:
            errors.append(f"{field.label} is required.")
        if len(value) > field.limit or "\x00" in value:
            errors.append(f"{field.label} exceeds its length limit or contains invalid characters.")
        if value.lstrip().startswith("="):
            errors.append(f"{field.label}: formulas are not accepted; paste values instead.")
        if value:
            try:
                if field.kind == "date":
                    # Native Excel dates are already ISO. Text follows the selected format.
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(T00:00:00)?", value):
                        value = date.fromisoformat(value[:10]).isoformat()
                    else:
                        value = datetime.strptime(value, DATE_FORMATS[job.date_format]).date().isoformat()
                elif field.kind == "datetime":
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError("timezone required")
                    value = parsed.astimezone(timezone.utc).isoformat()
                elif field.kind == "choice":
                    value = value.lower().replace(" ", "_")
                    if value not in field.choices:
                        raise ValueError("unsupported choice")
                elif field.kind == "score":
                    if value not in {"1", "2", "3", "4", "5"}:
                        raise ValueError("use 1–5")
                elif field.kind == "email":
                    value = value.lower()
                    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
                        raise ValueError("invalid email")
            except (ValueError, KeyError):
                hint = " Choose: " + ", ".join(field.choices) if field.choices else " Check the value/date format and timezone."
                errors.append(f"{field.label} is invalid.{hint}")
        data[key] = value
    errors.extend(date_range_errors(data))
    if data.get("date_of_birth") and data["date_of_birth"] > date.today().isoformat():
        errors.append("Date of birth cannot be in the future.")
    if job.record_type == "credential":
        warnings.append("Migration sign-off does not verify a credential; it remains pending evidence review.")
    if job.record_type in {"incident", "complaint"}:
        warnings.append("Historical import only. No notifications, reporting deadlines or external submissions are triggered.")
        if data.get("status") == "closed" and (not data.get("closed_at") or not data.get("outcome")):
            errors.append("A historical closed case needs its closure time and outcome.")
    for key in ("expiry_date", "review_date", "plan_end_date"):
        if data.get(key) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", data[key]) and data[key] < date.today().isoformat():
            warnings.append(f"{key} is in the past. The source date is retained.")
    if not data.get("source_reference"):
        warnings.append("No legacy reference: cross-file linking and exact repeat detection are limited.")
    return data, errors, warnings


def validate_row(session, row):
    data, errors, warnings = normalise(row.job, row.data)
    for field, (kind, _) in RELATIONS.items():
        if data.get(field) and not source_target(session, row.job.source_system, kind, data[field]):
            errors.append(f"{field}: no approved {kind} with that legacy reference in this organisation/source system. Import it first.")
    if row.job.record_type == "credential":
        ctype = session.scalar(select(CredentialType).where(
            func.lower(CredentialType.name) == data.get("credential_type", "").lower()))
        if not ctype:
            errors.append("Credential type is not in the configured catalogue.")
        elif ctype.has_expiry and not data.get("expiry_date"):
            errors.append("Expiry date is required for this credential type.")
    if data.get("source_reference"):
        for previous in row.job.rows:
            if previous.row_number >= row.row_number:
                break
            if previous.status != "skipped" and previous.data.get("source_reference") == data["source_reference"]:
                errors.append("Legacy reference repeats within this file. Correct it or skip one row.")
                break
    matches = candidates_for(session, row.job, data)
    row.candidates = [{"id": x.id, "label": label(x)} for x in matches]
    if row.decision == "update":
        target = next((x for x in matches if x.id == row.target_id), None)
        if target is None:
            errors.append("Select a current duplicate candidate before choosing update.")
        elif not row.target_snapshot or fingerprint(target) != row.target_snapshot:
            errors.append("Destination changed since review. Open the row and review it again.")
        if not row.decision_reason:
            errors.append("An update reason is required.")
        if not errors:
            # Blanks preserve existing values; validate exactly that merged result.
            # destination_values() reads row.data, so use its normalised form.
            row.data = data
            errors.extend(date_range_errors({**snapshot(target), **destination_values(session, row)}))
    elif row.decision == "create_new":
        if not row.decision_reason:
            errors.append("Explain why this is a separate record.")
        if data.get("source_reference") and source_target(session, row.job.source_system, row.job.record_type, data["source_reference"]):
            errors.append("That legacy reference already identifies a record. Update/skip it, or correct the reference.")
    elif matches:
        warnings.append("Possible duplicate: choose update, skip, or explicitly create a separate record.")
    row.data, row.errors, row.warnings = data, errors, warnings
    row.status = "invalid" if errors else ("duplicate" if matches and row.decision == "create" else "ready")
    return row


def apply_mapping(session, job, mapping, date_format, actor):
    if job.status != "mapping":
        raise MigrationError("Mapping is locked once rows have been staged.")
    if date_format not in DATE_FORMATS:
        raise MigrationError("Choose an explicit date format.")
    fields = DEFINITIONS[job.record_type]
    if set(mapping) - set(fields) or any(v not in job.headers for v in mapping.values()):
        raise MigrationError("Invalid source column mapping.")
    if len(set(mapping.values())) != len(mapping):
        raise MigrationError("A source column can be mapped only once.")
    if any(f.required and key not in mapping for key, f in fields.items()):
        raise MigrationError("Map every required field.")
    job.mapping, job.date_format = mapping, date_format
    for row in job.rows:
        row.data = {key: row.raw_data.get(column, "") for key, column in mapping.items()}
        validate_row(session, row)
    job.status = "review"
    audit(session, actor, "migration.mapped", "migration_job", job.id,
          {"mapped_fields": list(mapping), "ignored_columns": [h for h in job.headers if h not in mapping.values()]})


def edit_row(session, row, data, decision, target_id, reason, actor, target_snapshot=None):
    if row.status in FINAL or row.job.status in {"mapping", "cancelled"}:
        raise MigrationError("This row cannot be changed.")
    if decision not in {"create", "create_new", "update", "skip"}:
        raise MigrationError("Invalid duplicate decision.")
    if len(reason) > 2000:
        raise MigrationError("Keep the review reason under 2,000 characters.")
    if decision == "update":
        # Compare with the snapshot shown on GET, never a new snapshot taken on POST.
        record = session.scalar(select(MODELS[row.job.record_type]).where(
            MODELS[row.job.record_type].id == target_id).with_for_update()
            .execution_options(populate_existing=True)) if target_id else None
        if not record or not target_snapshot or fingerprint(record) != target_snapshot:
            raise MigrationError("Destination changed since the review page was opened. Reload and review the latest record before updating.")
    row.data, row.decision, row.decision_reason = data, decision, reason
    row.target_id = target_id or None
    row.target_snapshot = target_snapshot if decision == "update" else None
    if decision == "skip":
        if not reason:
            raise MigrationError("Record a reason for skipping this row.")
        row.status = "skipped"
    else:
        validate_row(session, row)
    audit(session, actor, "migration.row_reviewed", "migration_row", row.id, {"decision": decision})
    refresh_status(row.job)


def destination_values(session, row):
    values = {}
    data, kind = row.data, row.job.record_type
    for key, field in DEFINITIONS[kind].items():
        if key in {"source_reference", "credential_type", "reportability"} or key in RELATIONS:
            continue
        value = data.get(key)
        if not value:
            continue  # sparse update: blanks do not erase existing information
        if field.kind == "date":
            value = date.fromisoformat(value)
        elif field.kind == "datetime":
            value = datetime.fromisoformat(value)
        elif field.kind == "score":
            value = int(value)
        elif key == "is_active":
            value = value == "yes"
        values[key] = value
    for field, (entity, destination) in RELATIONS.items():
        if data.get(field):
            values[destination] = source_target(session, row.job.source_system, entity, data[field]).id
    if kind == "credential":
        values["credential_type_id"] = session.scalar(select(CredentialType).where(
            func.lower(CredentialType.name) == data["credential_type"].lower())).id
        values["status"] = "pending"
        # A correction cannot carry over a previous verification/approval.
        values.update(verified_by=None, verified_at=None, approved_by_user_id=None, approved_at=None)
    if kind in {"incident", "complaint"}:
        values["case_type"] = kind
        values["imported_at"] = utcnow()
        values["reportable_to_ndis"] = {"yes": True, "no": False, "requires_review": None}[data["reportability"]]
        values["reportability_decided_by"] = None if data["reportability"] == "requires_review" else row.approved_by
        values["reportability_decided_at"] = None if data["reportability"] == "requires_review" else utcnow()
    return values


def refresh_status(job):
    if job.status == "cancelled":
        return
    states = {r.status for r in job.rows}
    job.status = "complete" if states <= FINAL else ("partial" if "imported" in states else "review")


def approve_rows(session, job, row_ids, actor, signoff):
    if not signoff:
        raise MigrationError("Confirm you reviewed the selected records before approval.")
    if job.status in {"mapping", "cancelled"}:
        raise MigrationError("This job is not available for approval.")
    selected = [r for r in job.rows if r.id in set(row_ids)]
    if not selected or len({r.id for r in selected}) != len(set(row_ids)):
        raise MigrationError("Select rows from this job.")
    count = 0
    for row in selected:
        if row.status in FINAL:
            continue  # retries/double clicks cannot insert a second copy
        validate_row(session, row)  # relationships, duplicates and stale updates checked again
        if row.status != "ready":
            continue
        row.approved_by, row.approved_at = actor, utcnow()
        values = destination_values(session, row)
        model = MODELS[job.record_type]
        if row.decision == "update":
            record = session.scalar(select(model).where(model.id == row.target_id).with_for_update()
                                    .execution_options(populate_existing=True))
            if record is None or fingerprint(record) != row.target_snapshot:
                raise MigrationError("Destination changed. Review the update again.")
            before = snapshot(record)
            final_errors = date_range_errors({**before, **values})
            if final_errors:
                row.errors, row.status = final_errors, "invalid"
                row.approved_by = row.approved_at = None
                continue
            for key, value in values.items():
                setattr(record, key, value)
        else:
            record = model(**values)
            session.add(record)
            before = None
            if job.record_type in {"incident", "complaint"}:
                session.flush()
                record.reference = f"MIG-{record.id}"
        session.flush()
        if before is not None:
            session.add(MigrationChange(row_id=row.id, before=before, after=snapshot(record)))
        if row.data.get("source_reference"):
            identity = session.scalar(select(SourceIdentity).filter_by(source_system=job.source_system,
                entity_type=job.record_type, source_reference=row.data["source_reference"]))
            if identity and identity.destination_id != record.id:
                raise MigrationError("Legacy reference belongs to a different destination.")
            if not identity:
                session.add(SourceIdentity(source_system=job.source_system, entity_type=job.record_type,
                    source_reference=row.data["source_reference"], destination_id=record.id))
        row.destination_id, row.status = record.id, "imported"
        audit(session, actor, "migration." + ("updated" if before is not None else "created"),
              job.record_type, record.id, {"job_id": job.id, "row_id": row.id})
        count += 1
    refresh_status(job)
    audit(session, actor, "migration.signed_off", "migration_job", job.id,
          {"imported_this_approval": count, "selected": len(selected)})
    return count
