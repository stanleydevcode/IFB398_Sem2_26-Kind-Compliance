"""Map authenticated memberships to the roles used by the frontend layout."""

from flask import abort

from app import decorators
from app.constants import Roles


def current_prototype_role():
    membership = decorators.current_membership()
    if membership is None:
        abort(403)
    return {
        Roles.ORGANISATION_ADMIN: "admin",
        Roles.COMPLIANCE_MANAGER: "manager",
        Roles.STAFF_MEMBER: "staff",
    }[membership.role]
