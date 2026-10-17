from functools import wraps

from flask import abort, session
from flask_login import current_user

from app.constants import Roles
from app.models.identity import Membership
from app.services.permissions import can


def current_membership():
    organisation_id = session.get("organisation_id")

    if not current_user.is_authenticated or not organisation_id:
        return None

    return Membership.query.filter_by(
        user_id=current_user.id,
        organisation_id=organisation_id,
        is_active=True,
    ).first()


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            membership = current_membership()

            if membership is None:
                abort(403)

            if membership.role not in allowed_roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator


def capability_required(capability):
    """
    Allow access only when the current user's role
    has the requested capability.
    """

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            membership = current_membership()

            if membership is None:
                abort(403)

            if not can(membership.role, capability):
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator


admin_required = roles_required(
    Roles.ORGANISATION_ADMIN
)

manager_required = roles_required(
    Roles.ORGANISATION_ADMIN,
    Roles.COMPLIANCE_MANAGER,
)