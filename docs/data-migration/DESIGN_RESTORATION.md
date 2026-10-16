# Original frontend design restoration

This update uses the **original uploaded project ZIP** as the visual reference, while retaining the later connected-page functionality. The brand logo, font files, `theme.css`, `app.css` and shared `kc.js` remain byte-for-byte identical to that original source. The shared header/navigation and authentication flows retain their original structure. The existing Migration and assigned-participant links remain available.

## Apply the update

Use `Kind_Compliance_Design_Restored.zip` as an overlay on the merged project. It includes the earlier connected-page and startup fixes, so there is no need to apply those ZIPs first or afterwards. It assumes the original data-migration integration is already in the merged project, as in the latest uploaded ZIP.

1. Stop Flask. Commit/back up your current branch.
2. Extract the archive and merge its contents into the folder containing `run.py`. The ZIP has no enclosing project folder. Review teammate changes before replacing a shared file.
3. Keep `.env`, Docker configuration, your virtual environment and database. They are excluded from this overlay.
4. Run `python -m pytest -q`, then `python -m flask --app run.py run --debug` from your activated environment.
5. If the earlier migration-table upgrade was never applied, first run `python -m flask --app run.py migration-init`. This visual update adds no schema changes or dependencies.
6. Refresh the browser; use Ctrl+F5 if it retains older CSS. Existing approved records need no re-import.

The current [DESIGN_RESTORATION_MANIFEST.json](DESIGN_RESTORATION_MANIFEST.json) lists all packaged files, their hashes and their status against the latest merged project ZIP. Earlier integration/connected-page manifests describe earlier snapshots and are retained for history. Do not use their hashes to validate this update.

## Design changes

| Area | Restored or matched design |
| --- | --- |
| Workers | Original heading/subtitle, outlined import action, four counters, Register/Awaiting verification/Logins & access tabs, avatar/name cells and individual credential columns. An additional Other credentials column retains imported types such as CPR. |
| Worker profile | Original avatar/metadata header, screening/certificate cards, main content and contact sidebar. Working evidence uploads, verification and legacy references use those same components. |
| Participants | Original Participants/Notes tab strip, compact search toolbar and register columns. Last-note timestamps are queried for the visible authorised records. |
| Participant profile | Original 8/4 columns, care requirements, recent notes, plan panel, consent and support-team sidebar. New evidence actions and record links match the theme. |
| Documents | Original Library/Missing/Awaiting sign-off/Evidence tab presentation, compact table/search styling and upload icon. Existing pending/requirements URLs continue to work. Missing assessment remains explicitly unassessed. |
| Dashboard | Original score-number placeholders, counters, 8/4 task/expiry columns and active-risk panel. Values come from the live queries. |
| My compliance | Original counter strip, certificate/task panels, policy-acknowledgement empty state and account sidebar, with authorised credentials/originals and assignments. |
| New forms | Original panel headings, spacing, teal/outlined buttons, native inputs and dashed file-selection treatment. |
| Migration | Original theme colours, compact table styling, tabs and panel typography. Module-specific rules are scoped so migration CSS cannot restyle unrelated tables/panels. |

Original preview-only Add worker/Add participant, export, invitation, note-creation and consent-update controls have not been presented as functioning actions. Import/edit/upload operations remain available. The original worker-compliance/deployment labels were replaced with actual verification/date conditions because no agreed assessment engine exists yet.

## Code and documentation cleanup

- Added shared avatar, empty-state and credential-summary macros rather than copying those components between registers/profiles.
- Kept credential sign-off controls in a separate partial without changing CSRF/revision checks or review permissions.
- Query only the selected register tab; use bounded pagination, eager-loaded relationships and a grouped latest-note query.
- Apply the same tenant/assignment query to the Notes tab. Administrator login-link tabs remain unavailable to Compliance Managers and Staff Members.
- Updated the main README, frontend handoff and earlier installation pointers to reflect the current application.
- Repaired the static frontend preview utility to use disposable SQLite tables. It never connects to the configured PostgreSQL database, serves static output, and rejects POST requests.

## Verification

- **79 tests passed** against isolated SQLite databases, including existing migration, profile, versioning, assignment/revocation and cross-tenant checks.
- Two additional integration tests cover notes-tab search/assignment/tenant isolation and worker verification-queue/login-tab permissions.
- `python tools/preview_frontend.py --check` rendered **45 page/role combinations** successfully.
- Original theme CSS, base CSS, brand logo and shared shell JavaScript were compared directly against the original ZIP and are unchanged.

No browser engine or live PostgreSQL instance was available in this environment. Rendering and route tests verify HTML generation and behaviour; they do not establish pixel-perfect browser layout. Check the running app in your browser before merging.

## Local browser walkthrough

1. At desktop width, compare Dashboard, Workers, Participants, Documents and My compliance with the original design. Check tabs, counter strips, avatar cells and profile sidebars.
2. Open an imported worker/participant and confirm actual saved details, credential types and legacy references remain visible.
3. Switch Workers → Awaiting verification and, as Administrator, Logins & access. Check profile/edit links.
4. Switch Participants → Notes. As assigned staff, confirm only notes for assigned participants appear.
5. Upload and accept a document, then upload a replacement. Confirm pending/current versions and original downloads still work.
6. Open the migration mapping/review screens and check their tables/buttons fit the original theme.
7. Reduce the browser width to about 390 px. Check header navigation and wide tables scroll horizontally, forms remain usable, and profile columns stack.
8. Commit the reviewed source/docs on the data migration branch and Push origin. Use a pull request to merge into the shared branch.
