from app.constants import Roles

ROLE_CAPABILITIES = {
    Roles.ORGANISATION_ADMIN: {
        "manage_users",
        "manage_roles",
        "manage_staff",
        "verify_credentials",
        "manage_documents",
        "review_evidence",
        "manage_participants",
        "manage_incidents",
        "manage_risks",
        "manage_onboarding",
        "run_migration",
    },
    Roles.COMPLIANCE_MANAGER: {
        "manage_staff",
        "verify_credentials",
        "manage_documents",
        "review_evidence",
        "manage_participants",
        "manage_incidents",
        "manage_risks",
    },
    Roles.STAFF_MEMBER: {
        "view_own_compliance",
        "upload_own_credential",
        "report_incident",
        "view_assigned_actions",
    },
}

def can(role: str, capability: str) -> bool:
    return capability in ROLE_CAPABILITIES.get(role, set())
