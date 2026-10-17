# Connected Workers Participants and Documents pages

This update connects approved imports to the normal application pages. It builds on the merged project uploaded on 15 October 2026 and includes the previous startup/configuration fix. Records are read from the existing tenant tables; there is no second copy, synchronisation job or re-import step.

## Install

1. Stop Flask. Commit/back up the current checkout.
2. Extract Kind_Compliance_Design_Restored.zip into the repository root beside run.py. This is an overlay with only changed/new files. Review the manifest if teammates have edited those files since the last upload.
3. Keep your working .env and Docker mapping on port 5433. Neither is included in the ZIP.
4. From the existing (kind) terminal, run:

```powershell
python -m flask --app run.py db-check
python -m flask --app run.py migration-init
python -m pytest -q
python -m flask --app run.py run --debug
```

If db-check still selects 5432, set the correct process DATABASE_URL as described in STARTUP_FIX.md. Existing approved imports are already in the database: refresh the pages rather than importing them again. No new model columns or tables are introduced by this page update. migration-init is included above to ensure the earlier migration tables exist.

## What is connected

| Area | Behaviour |
| --- | --- |
| Workers /staff/ | Searchable, paginated real worker register including inactive historical workers, linked credential summaries and actual review/date counts. |
| Worker profile /staff/UUID | Saved contact/employment details, credentials/training catalogue entries, verification state, linked originals and historical versions, retained legacy references. |
| Worker edit | Validated profile changes with change reason, CSRF protection and stale-form detection. Permanent UUID and source mappings stay unchanged. |
| Participants /participants/ | Manager register with approved participant records, saved plan fields and key worker. Searchable and paginated. |
| Participant profile | Care requirements, plan/emergency details, existing notes/consents, linked evidence and manager-only legacy references. |
| Participant edit | Manager profile edits and key-worker assignment. Existing permission policy still reserves care-requirement edits for Compliance Managers. |
| Documents /documents/ | Library includes documents with an accepted current version. New pending documents appear only under Awaiting sign-off. |
| Document detail/upload | Upload, accept/return, replacement versions, dates, related profiles and hash-checked original downloads, using the same services as migration. |
| Dashboard | Live worker/participant/incident counts, accepted document count, credential/document review queues, credential dates and recorded open risks. |
| My compliance | The logged-in user's linked active worker profile, their credential records/accepted originals and their assigned participants. |

Worker review and date counts do not assert complete compliance or deployment eligibility. Audit readiness and compliance-health scores remain **Not assessed** because the client/team has not finalised the necessary applicability/scoring rules.

Dashboard incident/risk links open the existing migration live-record views. Building the separate incident/complaint and risk workflow screens is outside this update. This update also does not add manual worker/participant creation, progress-note creation, structured-consent creation, reminders, invites or account creation. Existing recorded notes/consents are displayed; original consent files are linked evidence rather than auto-created consent records.

## Approval and visibility

- Structured spreadsheet rows remain in Migration until approved. Only then do they exist in the normal worker/participant/credential tables.
- New document originals remain pending under Awaiting sign-off until accepted.
- A pending replacement leaves the current accepted version in the library and preserves its existing tracking dates.
- Accepting a replacement changes the current version. Historical originals remain downloadable by authorised managers.
- An expired historical original can be accepted for recordkeeping; its expiry condition remains expired.
- Evidence links do not automatically satisfy a configured requirement. The Evidence tab displays existing organisation requirements and recorded statuses.

The normal upload form accepts the same controlled file types/limits as migration. Originals uploaded through either path appear in the same document and profile views.

## Credentials and renewals

1. Open a worker and locate a credential imported into that profile.
2. Choose Upload supporting evidence, or Upload replacement evidence for a credential that already has a document.
3. Check the related-record selection refers to the credential itself. Enter the issue/expiry dates from the original.
4. Upload and accept the pending original from Documents after checking its contents and metadata.
5. The credential remains pending verification. An existing verified credential is reset to pending when its replacement original is accepted; it cannot inherit the old file's verification.
6. A Compliance Manager opens the worker profile, checks the accepted original/identity/type/dates, enters verification notes and ticks sign-off.
7. Record verification. The credential dates now use the accepted original's entered dates. An expiry date is required when the configured credential type requires one.

The earlier credential dates remain until this separate verification, so pending replacements do not silently rewrite them. Verification records retain the evidence-version ID, actor and old/new dates in the tenant audit log. A verified historical expired credential is still labelled expired. Verification is an authorised human review, not cryptographic signature validation or issuer lookup.

This preserves the supplied permission policy: Compliance Managers can verify credential renewals; Organisation Administrators can upload/accept document evidence but cannot use the credential-verification endpoint. Changing that role policy requires a separate agreed decision.

Replacement credential documents must retain their explicit credential association. The shared service rejects unlinking or reassigning an existing credential original to a different credential during replacement.

## Assigned participant access

The existing model has one key_worker_staff_id, not a general many-to-many assignment table. This implementation uses that field as the explicit access assignment. Wider support teams, temporary cover and delegated access need a separate model/policy decision.

An Organisation Administrator can open Workers → a profile → Edit details and link an **existing active organisation login** to the worker. This only sets Staff.user_id; it does not create an account, invite someone, grant/change a role or send a message. A login already linked to another worker in the same organisation cannot be reused. Compliance Managers cannot change this login mapping.

A manager then opens Participants → a profile → Edit details & assignment and selects the key worker.

A Staff Member with that linked, active worker profile can use My participants or My compliance to open their assigned participants. Access is enforced on each request:

- Participant details, plan/care/contact information and existing notes/consents are limited to managers or the assigned worker.
- Staff Members cannot open the all-participant register, other worker profiles, global Documents, or Migration.
- Staff see/download only **approved versions explicitly linked to that participant**. Permission is checked for each version, not just the logical document, preventing an old version linked to someone else from leaking through shared history.
- Reassignment, unlinking the worker's login, deactivating the worker, or deactivating membership removes access on subsequent requests.
- There is no fallback assignment by matching an email address.

Managers can also see pending linked originals. Legacy references and migration audit data stay manager-only. Existing service-agreement documents without a per-version participant association need that explicit association before assigned staff can download them through these routes.

## Edits and history

Worker/participant editors use the importer's shared field validation, while adding server-side checks for account links and worker assignments. Enter a reason before saving. A stale form is blocked and must be reloaded. Blank optional fields on normal edit forms intentionally clear those details; this differs from sparse migration updates, where blanks preserve existing values.

Profile edits keep UUIDs/source mappings intact. General edit audits contain actor, entity ID, changed-field names and the supplied reason, without duplicating sensitive care narratives. Detailed before/after snapshots remain available for reviewed migration updates under Migration.

## Acceptance walkthrough

### Existing imported data

1. Sign in as the test organisation's Administrator/Compliance Manager.
2. Open Workers. Previously approved staff should already appear. Open Alex's profile; credentials and legacy S-001 should be visible if the baseline examples were imported.
3. Open Participants and Casey's profile. Check the imported key worker, care/plan/contact fields and legacy P-001.
4. Edit a phone or job title with a reason. Save, refresh, and confirm the ID and legacy reference are unchanged. Importing the same legacy reference later should still produce a duplicate decision.

### Approval boundary

1. Stage a new staff row in Migration without approving it. Search Workers: it must not appear.
2. Approve the row. Search Workers again: it appears without another import or sync.
3. Upload a new policy through Documents. It appears under Awaiting sign-off, not the accepted library.
4. Accept it. The library and dashboard accepted-document count update.
5. Upload a replacement. Confirm the previous accepted version remains current until sign-off and remains downloadable afterwards.

### Linked evidence and verification

1. Upload participant evidence from the participant profile; accept the original in Documents. Return to the participant to download it.
2. Upload credential evidence from Alex's credential card; accept the original and confirm credential state is pending.
3. As a Compliance Manager, verify it from the worker profile. Check the credential dates against the accepted original.
4. Upload a replacement. Pending upload leaves prior accepted information unchanged. Accept the replacement: credential verification resets to pending. Verify again to apply the new original's dates.

### Access checks

1. Use an existing Staff Member account already provisioned for the test organisation; this update does not create accounts.
2. As Administrator, link that login to a worker. Assign that worker as Casey's key worker.
3. Sign in as that Staff Member. Check My participants, Casey's profile and an accepted participant original.
4. Try a participant assigned elsewhere: direct profile/file URLs must be denied. Global Workers/Documents/Migration must also be denied.
5. Reassign Casey or unlink/deactivate the worker. The previous worker's profile and file URLs must stop working after refresh.

## Verification and limits

The design-restoration update supersedes the initial visual layouts described here. See [current verification](DESIGN_RESTORATION.md).

The full updated suite passes **79 tests**, including eight connected-page integration tests and two register-tab access tests. Existing frontend tests now use real empty tenant tables rather than role-only mocks, and the obsolete disabled worker-import modal assertion now checks the working import link.

New tests cover staged-versus-live visibility, profile/provenance identity, stale forms, existing role restrictions, document acceptance/replacements, normal private downloads, dashboard counts, account linking, assigned access/revocation, cross-tenant URLs/forged relationships, credential renewal reverification, per-version confidentiality, search filters, HTML escaping and private response headers. They use separate attached SQLite schemas with the real tenant-session routing. The same migration test fixture supports the optional dedicated PostgreSQL test database described in README.md.

No live PostgreSQL instance or real browser engine was available here. Tests exercise Flask routes and rendered Jinja HTML; actual PostgreSQL execution and browser/mobile layout should be checked on the user's running app before merging. No claims of production security, malware scanning, statutory compliance, client-approved risk scoring or complete assignment policy are made.

The controlled storage, backup, retention and deployment limitations in the original migration README still apply.
