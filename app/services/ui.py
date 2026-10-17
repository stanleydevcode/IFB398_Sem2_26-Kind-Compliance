"""Presentation context for the shared shell; existing permissions stay in routes."""
from flask import url_for
from flask_login import current_user

from app import decorators
from app.constants import Roles
from app.services.permissions import can


def shell_context():
    membership = decorators.current_membership()
    role = membership.role if membership else None
    is_admin = role == Roles.ORGANISATION_ADMIN
    is_manager = role in (Roles.ORGANISATION_ADMIN, Roles.COMPLIANCE_MANAGER)
    navigation = []
    if is_manager:
        navigation.extend([
            ("Dashboard", "dashboard.index"),
            ("Documents", "documents.index"),
            ("Workers", "staff.index"),
        ])
    if is_manager:
        navigation.append(("Participants", "participants.index"))
    if membership and not is_manager:
        navigation.append(("My participants", "participants.assigned"))
    if membership:
        navigation.append(("Incidents", "incidents.index"))
    if is_admin:
        navigation.append(("Setup", "onboarding.index"))
    if can(role, "run_migration"):
        navigation.append(("Migration", "migration.index"))
    if current_user.is_authenticated:
        navigation.append(("My compliance", "my_compliance.index"))
    email = current_user.email if current_user.is_authenticated else ""
    search_index = [dict(label=label, kind="Page", url=url_for(endpoint)) for label, endpoint in navigation]
    return dict(
        ui_is_admin=is_admin,
        ui_is_manager=is_manager,
        ui_can_edit_care=can(role, "edit_participant_care_requirements"),
        ui_can_verify_credential=can(role, "approve_credential_renewal"),
        ui_navigation=navigation,
        ui_account_label=email,
        ui_initials=email[:2].upper(),
        ui_role_label={
            Roles.ORGANISATION_ADMIN: "Administrator",
            Roles.COMPLIANCE_MANAGER: "Compliance Manager",
            Roles.STAFF_MEMBER: "Staff Member",
        }.get(role, "Account"),
        ui_search_index=search_index,
    )
