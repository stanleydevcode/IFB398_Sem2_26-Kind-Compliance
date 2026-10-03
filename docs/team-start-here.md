# Team Start Here

## Branch/module split

Suggested branches:

- `feature/auth-staff`
- `feature/documents-evidence`
- `feature/incidents-risks`
- `feature/dashboard-onboarding`
- `feature/migration`

## Rule 1 — do not query tenant tables with the public session

Shared/public data:
- organisations
- users
- memberships
- reference/compliance metadata

Organisation-owned data:
- staff
- credentials
- participants
- documents
- evidence links
- incidents
- risks
- corrective actions
- notifications
- audit logs

Use `tenant_session()` for organisation-owned data.

## Rule 2 — permissions are backend rules

Do not rely on hiding buttons.
Routes must use role/capability checks.

## Rule 3 — migration should be preview-first

Do not import directly from spreadsheets into production tables.

Recommended flow:

1. Upload
2. Detect columns
3. Map fields
4. Validate
5. Show errors/duplicates
6. User approves
7. Import
8. Write audit log
9. Reconcile record counts

## Rule 4 — keep client-confirmed rules separate from assumptions

Examples still needing confirmation:
- staff deployment blocking rules
- credential approval authority
- incident reportability authority
- score formulas
- participant edit permissions
