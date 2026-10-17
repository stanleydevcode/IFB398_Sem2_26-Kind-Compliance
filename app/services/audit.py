from app.models.operations import AuditLog

def add_audit_entry(tenant_db, *, user_id, action, entity_type, entity_id=None, details=None):
    tenant_db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )
