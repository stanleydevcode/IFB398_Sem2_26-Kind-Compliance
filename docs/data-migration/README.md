# Kind Compliance data migration

**Current update:** use `Kind_Compliance_Design_Restored.zip` and [DESIGN_RESTORATION.md](DESIGN_RESTORATION.md) for the latest cumulative overlay.

**Connected-page update:** approved records now appear on Workers, Participants and Documents. See [CONNECTED_PAGES.md](CONNECTED_PAGES.md) for the normal page workflows, access rules, renewal verification and current verification results.

This integration adds a working migration workspace to the supplied Flask application. It uses the existing PostgreSQL schema per organisation, existing login/membership roles and the team's actual Staff, StaffCredential, Participant, Case, Risk, Document and DocumentVersion models. It replaces the migration placeholder; it does not replace the team's authentication or domain architecture.

The two uploaded handoffs supplied the requirements. Where their older recommendations differ, the newer development handoff's confirmed client answers take priority. Exact mandatory fields, status vocabularies, partial sign-off rules and duplicate identity rules still require client/team acceptance. This is a development implementation for review, not a claim that the client has approved those choices.

## Install into your working checkout

1. Commit your current work or make a backup. Stop Flask with Ctrl+C.
2. Extract the integration ZIP into the repository root (the folder containing `run.py`). Allow the listed source files to be replaced. There is no extra parent folder in this ZIP.
3. Keep your working `.env` and Docker port configuration. They are deliberately excluded. Your database connection should still use `127.0.0.1:5433` if you applied the startup fix from this conversation.
4. If teammates changed any of the replaced files after the uploaded ZIP, merge those changes using `CHANGELOG.md`; do not overwrite their work blindly.

From the root in your existing `(kind)` PowerShell terminal:

```powershell
python -m pip install -r requirements.txt
docker compose up -d
python -m flask --app run.py migration-init
```

`migration-init` creates only the five new migration tables in every existing organisation schema. It is safe to repeat. It does not drop data, alter existing domain columns or reset PostgreSQL credentials. The normal `init-db` command only creates public/shared tables, so it is not a substitute for this upgrade on an existing account.

To upgrade one organisation only:

```powershell
python -m flask --app run.py migration-init --organisation-id YOUR-EXISTING-ORGANISATION-UUID
```

For a completely new database, run the original README's `init-db`, start the app and register an organisation. Registration automatically provisions the new tenant tables with the existing domain tables.

Configure the credential catalogue before importing the fictional credential file. These developer commands add shared reference types, preserving existing types/expiry rules:

```powershell
python -m flask --app run.py migration-add-credential-type "First Aid"
python -m flask --app run.py migration-add-credential-type "CPR"
python -m flask --app run.py migration-add-credential-type "Worker Screening"
python -m flask --app run.py run --debug
```

Use client-approved names in real deployments. `--no-expiry` is available for a type that genuinely does not require an expiry date. Uploads cannot create or modify shared catalogue types.

Open <http://127.0.0.1:5000/migration/>. Log in as an **Organisation Administrator** or **Compliance Manager**. Both can upload, correct, decide duplicates, approve imports and review documents. Staff Members have no access to this workspace, its templates, exports or originals. Imported staff rows create staff profiles only; they never create login accounts or grant roles.

## Spreadsheet workflow

1. Choose **Import spreadsheet** and the destination record type.
2. Enter a source system name, such as `Legacy demo`. Reuse the exact same name across related exports; references are case-sensitive within that source.
3. Upload one UTF-8 CSV or one-sheet XLSX. The first row contains headings. Limits: 10 MiB/file, 2,000 source rows, 80 columns and 10,000 characters/cell. Legacy `.xls` should first be saved as `.xlsx` or UTF-8 CSV. Multiple worksheets must be exported separately.
4. Map each required target field to a source column. Exact canonical headings are suggested. Choose the format for text dates explicitly. Unmapped columns remain in the raw row/original but are not copied into live fields. No organisation/user IDs from a source file control ownership.
5. Validate and inspect the review queue. Invalid rows show actionable errors; possible duplicates require a decision. Valid rows become **ready**, not live.
6. Use **Review row** to correct values, revalidate unresolved relationships or record a duplicate decision. Already imported/skipped rows cannot be changed through staging.
7. Select ready rows (the header checkbox selects the current page only), read the values/warnings, tick sign-off and approve. Only approved rows are written to the domain tables. Invalid/duplicate rows remain for later work. This partial approval behaviour is an implementation choice to reconcile the client's two requirements and needs acceptance.
8. Download the reconciliation CSV and original source. The CSV reports source row, legacy reference, state, decision, destination UUID, errors/warnings, reviewer and approval time. Use the live-record tabs to verify the resulting database records.

Import staff before participants/credentials/risks/cases that refer to them. Import participants before incidents/complaints that refer to them. Related rows must already be approved; staged rows do not count as valid relationship targets. After importing a dependency, open the waiting row and save it to revalidate.

Native Excel dates and ISO dates are accepted regardless of the text-date choice. Corrections entered on the row review screen can always use YYYY-MM-DD. Incident timestamps must include an explicit offset, e.g. `2024-08-12T09:15:00+10:00`, and are normalised to UTC. Keep identifiers, phone numbers and NDIS numbers as text in Excel to preserve leading zeroes. Formulas are never evaluated: mapped formula values are validation errors; paste static values instead.

## Supported destinations

| Type | Required MVP fields | Related data / important behaviour |
| --- | --- | --- |
| Staff | first_name, last_name | Email/contact, job title, employment type/start date, active flag. No user/login/permissions created. |
| Participants | first_name, last_name | DOB, source NDIS identifier, support/care requirements, plan dates, emergency contact, key worker reference. |
| Staff credentials | staff_reference, credential_type; expiry_date if required by catalogue | Issue/expiry dates. Imports and corrections are pending; old verification/approval is cleared on correction. Original evidence is attached separately. |
| Historical incidents | category, description, occurred_at, reported_at, severity, status, reportability | Reporting staff/participant legacy references, location, response, investigation, outcome, historical closure. |
| Historical complaints | Same as incidents | Uses `Case(case_type='complaint')`; remains distinct from incidents. |
| Risks | title, status | Owner reference, description, category, 1–5 likelihood/consequence, source ratings, controls/treatment, review date. No risk matrix is invented. |

For the complete machine-readable field and choice definitions, see `app/services/migration/definitions.py`. Blank CSV templates are also downloadable inside the authenticated workspace and included in `examples/migration/templates/`.

Optional missing information is kept missing. Mandatory rules are practical MVP defaults, not an asserted NDIS field standard. Unmapped witnesses, additional emergency contacts, original authors or other unsupported attributes stay in the original/raw source only. They do not automatically become relational fields in a register. Import does not create structured participant consents or corrective-action rows; originals can be retained and linked to the participant/case for subsequent entry through those modules.

## Duplicates and reviewed changes

Candidates are detected by a legacy reference plus source system/type, and by conservative natural matches: staff email/name, participant identifier/name, risk title, case type/description or staff/credential type. These rules flag possibilities; they do not prove identity.

- **Create if no duplicate**: no silent overwrite. Rechecked at approval time.
- **Update existing candidate**: inspect candidate values, choose the target and provide a reason. Only non-empty mapped fields change. The permanent UUID is preserved. Before/after values are retained in a restricted change table. Blank fields never silently erase live information.
- **Create a separate record**: requires a reason. If a source reference already identifies another record, correct that reference or choose update/skip. A single legacy identity cannot point to two destinations.
- **Skip**: requires a reason and leaves the source row traceable without creating a destination.

Updates whose destination changed since review are blocked until re-reviewed. Repeat confirmation of an imported row is idempotent. PostgreSQL approval writes take an organisation-scoped transaction advisory lock, serialising this module's concurrent jobs and rechecking candidates. Existing domain screens do not take that advisory lock; future manual-create services should share duplicate rules/constraints. The unique source identity constraint provides an additional database guard.

A repeated legacy reference within one file leaves the later row invalid until corrected or one row is skipped. If a dependency or duplicate decision changes, save the affected row to refresh validation.

One approval request is a transaction: all selected ready writes, their provenance and audits commit together; unexpected failure rolls them all back. Invalid or newly conflicting rows are left in review while other ready selected rows can proceed. There is no post-commit automatic undo. Correct an imported record through a reviewed update; cancellation is available only before a job imports anything.

## Original documents and versioning

Open **Documents & versions**. Supported retained formats: PDF, DOC/DOCX, JPG/JPEG, PNG, TIFF, CSV and XLSX. This is original-file support, not automatic parsing or browser preview for every format. Email attachments can be saved and uploaded; full `.eml`/`.msg` messages are not imported.

1. Choose the original and enter title/kind/category and any legacy reference.
2. Enter issue, expiry and/or next review dates manually. These are structured fields separate from the file content.
3. Optionally link a current tenant staff/participant/credential/incident/complaint/risk record and an existing organisation requirement.
4. Upload. The logical document is draft and the immutable version is pending.
5. Download/check the original, enter review notes, tick sign-off and accept it, or return it for correction.
6. Acceptance sets the logical document's current version and its structured tracking dates. A requirement link is created as `linked` for the existing evidence-review process; requirement satisfaction is not inferred.
7. For renewal/replacement, use **Upload a new version** on that document. The earlier accepted version remains current until the replacement is accepted. All earlier original files remain retained. An older pending version cannot supersede an already accepted newer one.

Identical retained file bytes are flagged on version review pages; reviewers decide whether to accept or return them. No file/document merge is automatic.

A credential attachment links its Document after file acceptance; it does not mark the StaffCredential verified. Record approval, evidence acceptance, credential verification and date condition are distinct. Historical expiry/review dates are preserved, with expired/overdue/due-within-30-days labels shown separately. Accepting an expired original is possible for historical recordkeeping and does not make its dates current.

Links for participants, staff, risks and cases are retained on the migration attachment sidecar. Credential links also populate `StaffCredential.document_id`. Requirement links create the existing `EvidenceLink`. The normal worker and participant profiles now display sidecar evidence links. The separate case workflow screens still need their own evidence panel integration.

## Test the fictional historical files

Everything under `examples/migration/` is invented for testing, including names, identifiers, contact details, narrative text and certificate content. PDF/Word/scan files visibly say **FICTIONAL TRAINING SAMPLE - NOT VALID EVIDENCE**. No real signed certificate or client/provider records are included.

Use a test organisation and source system `Legacy demo`. Import these in order:

| File under examples/migration/history | Expected on a clean test organisation |
| --- | --- |
| 01_staff_history.csv | 3 ready staff rows, including one inactive historical worker |
| 02_participants_history.csv | 2 ready participants after staff approval |
| 03_credentials_history.csv | 3 ready credentials after staff approval/catalogue setup; all remain pending verification; C-001 expired as of 15 Oct 2026 |
| 04_incidents_history.csv | 2 historical incidents, one closed and one investigating |
| 05_complaints_history.csv | 1 historical closed complaint |
| 06_risks_history.csv | 2 risks, one with an overdue review as of 15 Oct 2026 |
| 09_provider_columns_staff.csv OR .xlsx | 2 additional staff; use the mapping below; import one alternative only |

The first six files produce **13 live domain records** in total (3+2+3+2+1+2). They do not create accounts, notifications or inferred compliance results.

Provider-style heading mapping (also supplied in `09_column_mapping.json`):

| Source | Target |
| --- | --- |
| Worker ID | source_reference |
| Given Name | first_name |
| Surname | last_name |
| Contact Email | email |
| Position | job_title |
| Started | start_date |

Choose **DD/MM/YYYY** for the provider-style CSV. Its XLSX alternative contains real Excel date cells. The JSON file is a human-readable mapping guide; there is no JSON mapping upload endpoint.

Review cases, after the first six files have been approved:

- `review_cases/07_staff_needs_review.csv`: one ready row, one duplicate of S-001 and three invalid rows (missing name, bad email, repeated S-004 reference). Approve the ready row while leaving others queued. Correct an invalid row, skip the repeated row or review S-001 explicitly.
- `review_cases/08_staff_reviewed_update.csv`: duplicate S-001. Choose update, select Alex Example and record a reason. Approval changes the job title while preserving the staff UUID; before/after values remain available in row history.
- `review_cases/10_incident_bad_dates.csv`: blocked for missing timezones, unsupported severity and incomplete closure information.
- `review_cases/11_duplicate_headers.csv`: rejected before staging because duplicate headings would lose column meaning.
- Re-upload an already approved baseline file: rows are duplicates and are not automatically inserted/overwritten.

Document exercise:

1. Upload `documents/policy_v1_2024.pdf` as a policy titled `Document control policy`, legacy POL-001, issued 2024-01-15 and review 2025-01-15. Accept it. Its date label remains review overdue.
2. From that document choose a new version, upload `policy_v2_2026.docx`, issued 2026-10-01 and review 2027-10-01. Confirm version 1 stays current while version 2 is pending. Accept version 2 and download version 1 again.
3. Upload `first_aid_expired_C001.pdf` as a credential document, issued 2023-06-01 and expiry 2026-06-01, linked to imported credential C-001. Accept the original. Confirm expiry remains historical and credential verification stays pending.
4. Upload `historical_incident_form_INC2024001.pdf` or its `scanned_incident_INC2024001.png` rendition, linked to INC-2024-001. The original is retained; no PDF/image fields are extracted automatically. This is a digital rendition for testing image upload, not an authentic physical scan.

## Storage, access and recovery

The server writes random-key files outside `static/` under `instance/migration_private/<tenant schema>/`. Original filenames are metadata, not paths. Every download checks the active membership, tenant schema, record ID, allowed path and stored SHA-256 before returning an attachment. Workspace responses are private/no-store. Every migration POST checks a session CSRF token. There is no public file URL.

Optionally set `MIGRATION_STORAGE_ROOT` in your Flask configuration. Back up that private directory **and PostgreSQL together**; file references in the database do not replace the original bytes. Local originals are immutable through application routes, but this is not WORM storage: server administrators/filesystem access can still change them. Integrity checks detect changed bytes, not restore them.

Uploads check size, extension and basic signatures/Office archive expansion. These checks are not malware scanning or a full content-sanitisation system. There is no OCR, automatic signature verification, full-text search, email/API connector, bulk attachment manifest, encryption-at-rest implementation, retention purge or cleanup scheduler in this release. Use appropriate storage protection, malware scanning, backups, deployment security and approved retention rules before processing real provider information. Aborted processes can leave unreferenced files; reconciliation/cleanup should be reviewed before deletion, never automatically discard historical evidence.

General audit entries contain actor IDs, operation, job/row/destination IDs and file hashes. Raw source rows and before/after values can contain sensitive information and remain tenant-scoped in the migration tables. They require the same retention/access treatment as the underlying records.

## Historical cases and team boundaries

`occurred_at` stores the event time; for this importer, `reported_at` stores the provider-awareness/reported time supplied by the reviewer. If the source distinguishes first awareness from formal report creation, resolve that mapping with the incident teammate; do not substitute upload time. `imported_at` records the migration time separately. Timestamps are retained in UTC. Closed historical cases require an outcome and original closure time. `requires_review` stores reportability as unknown; yes/no requires the importing manager's sign-off. No legal reporting countdowns or external reports are produced.

Workers, Participants, Documents, My compliance and dashboard record counts are now connected to the real tenant tables. Restricted live-record views remain under Migration for reconciliation. Staged spreadsheet rows do not enter the normal registers or dashboard totals. The separate incident and risk workflow pages remain outside this update; dashboard links for those records use the existing migration record views. See CONNECTED_PAGES.md for details.

Participant details in the migration workspace remain manager-only. Normal participant profiles now enforce access using the existing key-worker assignment and explicit Staff.user_id login link. Approved participant originals have per-version access checks. See CONNECTED_PAGES.md for the assignment policy and limits.

## Testing

Run all original and migration tests from the repository root:

```powershell
python -m pytest -q
```

Migration tests exercise the real Flask routes, authentication/memberships, CSRF, tenant sessions with separate attached SQLite schemas, partial approval, reviewed updates, idempotency, dependency checks, cross-tenant denial, unexpected rollback, original retention/integrity and document version approval.

The exact local verification result is recorded in `VERIFICATION.md`. PostgreSQL verification is opt-in against a **disposable test database**: tests drop/recreate its public and fixture tenant schemas. Its name must end in `_test`. Never point this variable at a provider/development database containing work.

```powershell
docker compose exec db createdb -U kind kind_migration_test
$env:MIGRATION_TEST_DATABASE_URL = "postgresql+psycopg://kind:kind@127.0.0.1:5433/kind_migration_test"
python -m pytest tests/migration -q
Remove-Item Env:MIGRATION_TEST_DATABASE_URL
```

Use your actual mapped port. This does not alter the application's DATABASE_URL. Browser automation is optional and is not a runtime dependency.

## Client/team review still needed

Confirm per-type mandatory fields and statuses; meaning of partial sign-off; duplicate identity rules; credential catalogue/expiry rules; mapping of source awareness/report times; historical yes/no reportability provenance; how participant consent and multiple witnesses/contacts are represented; retention/archive policies; approved evidence applicability by registration group; and integration of sidecar evidence links and approved records with normal domain screens/dashboard calculations.

The client handoff contains conflicting document baseline/checklist descriptions. This module deliberately does not assign a universal missing-document count or auto-satisfy requirements from uploads. Existing configured organisation requirements can be linked for later authorised review.
