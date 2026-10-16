# Verification record

This is the original migration verification record. The later connected-page update and current 79-test result are documented in CONNECTED_PAGES.md.

Verified 15 October 2026 against the uploaded project snapshot, using Python 3.12 and its pinned requirements.

## Automated result

`python -m pytest -q`: **63 passed** (42 original tests plus 21 migration tests).

Migration coverage includes:

- Real Flask request routes, Jinja page rendering, active membership roles and session CSRF protection.
- Separate attached SQLite tenant schemas using the application's real tenant_bind/tenant_session functions; no mock tenant filter is substituted.
- Upload, mapping, explicit date handling, validation, partial approval and row correction.
- Staff/participant/credential/case/risk writes to existing domain models; no generic demo destination table.
- Duplicate review, explicit update, create-separate-record restrictions, source-identity preservation, repeated approval and a cross-job duplicate race sequence.
- Stale destination updates, stale review forms, sparse updates preserving an inactive worker and full rollback after a simulated later-row failure.
- Manager access; Staff Member/anonymous/cross-organisation denial; private originals and exports.
- Dependencies scoped to approved records in the correct tenant/source system.
- Original-file retention, checksums, invalid/oversized uploads, Office archive validation, duplicate file indicators, pending replacement behaviour and rejection of superseded older pending versions.
- Credential evidence linking without granting verification.
- End-to-end imports of every baseline historical CSV fixture and the supplied XLSX with native dates.
- Reconciliation CSV formula-injection escaping, repeated source references and additive CLI setup/catalogue commands.

The five new table definitions also compiled with SQLAlchemy's PostgreSQL dialect, and all application/test Python files passed compileall.

## Artifact review

- Three fictional PDF originals rendered and visually checked, one page each.
- Fictional policy DOCX rendered and visually checked, one page.
- Incident image rendition visually checked.
- One-sheet historical XLSX rendered/inspected, then read by the actual importer and imported through Flask in the fixture test.
- All document fixture formats passed the upload validator.

## Verification limits

A native PostgreSQL server was not available in this execution environment. PostgreSQL DDL compilation is not a substitute for execution. PostgreSQL-specific schema creation, foreign keys, advisory-lock concurrency and production transaction behaviour still require the optional disposable-database run documented in README.md. The test fixture supports the real PostgreSQL backend through MIGRATION_TEST_DATABASE_URL.

Authenticated routes/templates were exercised through Flask's test client. A browser engine could not be installed here, so no browser screenshot, interactive browser or mobile visual verification is claimed. The migration pages reuse the existing Bootstrap theme and include a small scoped stylesheet; inspect them on the user's running app before merging.

No real provider data, NDIS submissions, live email, external integrations, production deployment, GitHub push or merge was performed. Production storage controls, malware scanning, backups/restore, retention policies and the rest of the application's security remain deployment/team responsibilities.
