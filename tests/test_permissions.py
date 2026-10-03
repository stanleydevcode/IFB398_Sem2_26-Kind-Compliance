from app.constants import Roles
from app.services.permissions import can

def test_admin_can_manage_users():
    assert can(Roles.ORGANISATION_ADMIN, "manage_users")

def test_staff_cannot_manage_users():
    assert not can(Roles.STAFF_MEMBER, "manage_users")

def test_staff_can_report_incident():
    assert can(Roles.STAFF_MEMBER, "report_incident")
