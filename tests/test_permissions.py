from app.constants import Roles
from app.services.permissions import can


def test_admin_can_manage_users():
    assert can(
        Roles.ORGANISATION_ADMIN,
        "manage_users",
    )


def test_staff_cannot_manage_users():
    assert not can(
        Roles.STAFF_MEMBER,
        "manage_users",
    )


def test_staff_can_report_incident():
    assert can(
        Roles.STAFF_MEMBER,
        "report_incident",
    )


def test_compliance_manager_can_approve_credentials():
    assert can(
        Roles.COMPLIANCE_MANAGER,
        "approve_credential_renewal",
    )


def test_admin_cannot_approve_credential_renewal():
    assert not can(
        Roles.ORGANISATION_ADMIN,
        "approve_credential_renewal",
    )


def test_compliance_manager_can_edit_care_requirements():
    assert can(
        Roles.COMPLIANCE_MANAGER,
        "edit_participant_care_requirements",
    )


def test_staff_cannot_edit_care_requirements():
    assert not can(
        Roles.STAFF_MEMBER,
        "edit_participant_care_requirements",
    )


def test_only_admin_can_record_commission_reference():
    assert can(
        Roles.ORGANISATION_ADMIN,
        "record_commission_reference",
    )

    assert not can(
        Roles.COMPLIANCE_MANAGER,
        "record_commission_reference",
    )


def test_only_compliance_manager_can_close_incident():
    assert can(
        Roles.COMPLIANCE_MANAGER,
        "close_incident_case",
    )

    assert not can(
        Roles.ORGANISATION_ADMIN,
        "close_incident_case",
    )