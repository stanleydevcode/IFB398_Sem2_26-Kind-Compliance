# Integration file map

Based on the uploaded IFB398 project snapshot dated 15 October 2026. The overlay contains only changed/new files, not the whole repository.

## Existing files updated

| File | Change |
| --- | --- |
| app/blueprints/migration/routes.py | Replace placeholder with authenticated tenant-scoped import/review/document routes. |
| app/models/__init__.py | Register new migration models with existing metadata/provisioning. |
| app/cli.py | Register additive migration setup and credential catalogue commands. |
| app/services/permissions.py | Allow Compliance Manager to run migration, alongside Administrator. |
| app/services/ui.py | Add Migration navigation for authorised managers. |
| app/templates/base.html | Show migration account link to both manager roles. |
| app/templates/documents/index.html | Link existing Documents page to working upload/version workspace; identify remaining overview placeholder. |

## Added files

- `app/models/migration.py`: five tenant tables; no changes to existing domain table definitions.
- `app/services/migration/`: field definitions, bounded readers, shared validator/import service, private file storage, document version lifecycle and setup commands.
- `app/templates/migration/`: workspace, mapping, review, correction, reconciliation, document history and restricted live-record verification views.
- `app/static/css/migration.css` and `app/static/js/migration.js`: small scoped stylesheet and select-ready-page behaviour.
- `tests/migration/`: route/service/security/schema isolation tests, optional PostgreSQL backend.
- `examples/migration/`: blank templates, fictional historical exports, review cases, original document fixtures and sample guide.
- `docs/data-migration/`: usage README, verification record and this change list.
- `MIGRATION_START_HERE.md`: short overlay setup guide.

Existing tenant provisioning already builds all registered tenant metadata for new organisations. `migration-init` adds only the new tables to existing organisation schemas. No pre-existing migration directory or Alembic revisions were present in the supplied snapshot; this is deliberately an additive, idempotent command rather than an invented Alembic revision chain.

Unchanged: database credentials/ports, environment files, requirements, login/register implementation, normal dashboard/staff/participant/case/risk routes, existing domain table columns and the old unused `app/services/importers.py` preview helper. No remote repository was pushed or merged.
