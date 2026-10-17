# Migration review fixes: feedback issues 2 and 3

This patch is based on the uploaded `IFB398_Sem2_26-Kind-Compliance (2).zip`. It changes only migration validation/review handling, regression tests and these notes. Your repaired `app/services/permissions.py` is unchanged and is excluded from the overlay.

## Install

1. Stop Flask with Ctrl+C and commit/back up your current branch.
2. Extract `Kind_Compliance_Migration_Review_Fixes.zip` and copy its contents into the existing repository root beside `run.py`. Merge folders and replace the included files. Review teammate edits to those files before replacing them.
3. In the activated `(kind)` PowerShell terminal, run:

```powershell
python -m pytest -q
python -m flask --app run.py run --debug
```

Refresh/reopen any migration review forms that were open before restarting. Old forms do not contain the new review context and cannot submit update decisions until reloaded. No new package, database migration, re-import or database reset is needed. `.env`, Docker configuration, existing database records and the frontend design are not changed.

## Issue 2: validate the final partial update

Blank import fields still preserve existing values. Date-range validation now checks the resulting record after combining the imported fields with those preserved values, not just the uploaded row.

The same checks apply to credential issue/expiry dates, participant plan start/end dates, and incident/complaint occurrence versus reporting/closure times. Datetimes are compared in UTC, including UTC timestamps returned without timezone information by SQLite.

Invalid merged dates leave the row invalid and the destination unchanged. The resulting values are revalidated at approval, including updates that were already queued by the old implementation. The locked destination is refreshed before the final fingerprint/date checks; valid sparse updates still preserve IDs, unmapped fields, provenance and before/after history.

This prevents new invalid imports. It does not automatically repair date ranges already saved by a previous version; review and correct any affected records.

## Issue 3: compare with what the reviewer saw

The review page now includes a signed context containing the displayed candidates' fingerprints and the organisation/job/row/revision scope. Only identifiers and fingerprints are included; full source/candidate records are not embedded in this hidden context.

When submitting Update, the selected target must have appeared on that page and must still match its displayed fingerprint. If it changed after the page opened, the request is rejected and the reviewer must reload and inspect the new values. Missing, altered or different-row contexts are rejected too. The engine no longer silently captures a new target fingerprint when the form is submitted.

The migration-row revision also includes the saved target fingerprint. Existing approval-time protection remains, with the locked target refreshed to avoid a stale SQLAlchemy identity-map copy.

## Manual checks

### Partial plan dates

1. Use an existing test participant with plan start `2026-10-01` and plan end `2027-10-01`.
2. Import an update identified by the same source system/legacy reference. Include the required names and only plan end `2026-01-01`; leave plan start blank/unmapped.
3. Review the row, select Update and the existing participant, and enter a reason.
4. The row must become invalid with `plan_end_date cannot precede plan_start_date`. Approval must leave both stored dates unchanged.
5. Correct the end date to `2028-10-01`, save a freshly reviewed decision and approve. The start stays `2026-10-01`; the end becomes `2028-10-01`.

### Destination changed while a form is open

1. Stage a duplicate worker row and open its Review row page. Inspect the existing candidate.
2. In another browser session/tab, edit and save the existing worker's name through Workers.
3. Submit Update from the original migration review page.
4. It must reject the stale decision with a reload/review message. The newer worker name must remain unchanged.
5. Reload the review page, inspect the updated candidate and explicitly resubmit. Approval may now apply the reviewed update.
6. Also check a change made after saving the decision but before approval; the existing approval-time guard must still block the overwrite.

## Verification

- **90 tests passed** in the full SQLite suite.
- **11 additional regression scenarios** cover both partial-plan endpoints, a valid sparse extension, credential issue/expiry merging, incident/complaint retained closure times, changes between opening/submitting review, fresh-review recovery, queued pre-patch updates and missing/tampered/different-row contexts.
- Before the changes, the initial seven regression scenarios produced **six failures and one pass** against the uploaded code.
- The static frontend preview rendered **45 page/role combinations** successfully.
- The migration test directory now contains **42 tests**. The fixture still supports an optional dedicated PostgreSQL database.

PostgreSQL execution was not completed here: a temporary PostgreSQL 16.2 binary was available, but this environment prevented starting it under a non-root user. The prior feedback's PostgreSQL results describe the earlier code, not this patch. Re-run the PostgreSQL suite in your existing disposable test environment before merging.

For that optional check, set `MIGRATION_TEST_DATABASE_URL` to your separately provisioned disposable database ending in `_test`, then run `python -m pytest -q tests/migration`. The fixture creates/drops schemas in that database; do not point it at the working application database. Remove that test-only environment variable after testing.

## Included files

- `app/services/migration/engine.py`
- `app/blueprints/migration/routes.py`
- `app/templates/migration/row.html`
- `tests/migration/test_workflow.py` (test helper submits the actual signed form context)
- `tests/migration/test_review_integrity.py`
- `MIGRATION_REVIEW_FIXES.md`
