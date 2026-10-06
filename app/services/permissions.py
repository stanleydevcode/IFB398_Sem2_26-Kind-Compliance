from app.constants import Roles

ROLE_CAPABILITIES = {
    Roles.ORGANISATION_ADMIN: {
        "manage_users",
        "manage_roles",
        "manage_staff",
        "manage_documents",
        "review_evidence",
        "manage_participants",
        "manage_incidents",
        "manage_risks",
        "manage_onboarding",
        "run_migration",

        # Confirmed by client
        "decide_incident_reportability",
        "record_commission_reference",
    },

    Roles.COMPLIANCE_MANAGER: {
        "manage_staff",
        "manage_documents",
        "review_evidence",
        "manage_participants",
        "manage_incidents",
        "manage_risks",

        # Confirmed by client
        "approve_credential_renewal",
        "approve_policy_version",
        "edit_participant_care_requirements",
        "decide_incident_reportability",
        "close_incident_case",
    },

    Roles.STAFF_MEMBER: {
        "view_own_compliance",
        "edit_own_contact_details",
        "upload_own_credential",
        "report_incident",
        "view_assigned_actions",
    },
}


def can(role: str, capability: str) -> bool:
    return capability in ROLE_CAPABILITIES.get(role, set())