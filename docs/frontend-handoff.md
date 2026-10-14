# Jesse's frontend handoff

## Current scope

The existing Flask login, registration, role decorators, organisation setup and
shared layout remain in place. This branch adds Jinja presentation for the pages
below, following Douglas's prototype design. The prototype source is on
`douglas/prototype-source/prototype`; its fictional records and fixed 2026 dates
are not copied into the application.

| Page | Template | Current state |
| --- | --- | --- |
| Shared layout | `app/templates/base.html` | Theme, navigation, authenticated account menu and existing POST logout |
| Workers | `app/templates/staff/index.html` | Register, search/filters, verification and login tabs, empty states and local form previews |
| Workers import | Modal in `staff/index.html` | File chooser; review/import remains unavailable until Justin's migration service is connected |
| Participants | `app/templates/participants/index.html` | Register, notes, search/filters, empty states and local form previews |
| Organisation setup | `app/templates/onboarding/index.html` | Blank profile, insurance, groups and personnel forms; local preview only |
| Dashboard | `app/templates/dashboard/index.html` | Unassessed scores and empty task/risk sections |
| Documents | `app/templates/documents/index.html` | Library and evidence tabs with empty states |
| Incidents | `app/templates/incidents/index.html`, `incidents/new.html` | Role-specific empty register and blank report form; no submission endpoint |
| My compliance | `app/templates/my_compliance/index.html` | Empty certificates/tasks and signed-in user's account details |

No fictional worker, participant, incident, document, task, score or migration
result is shown. A dash means a count has not been connected to real data; it
does not mean zero. Form previews do not persist, send mail or upload files.
Detail templates for workers and participants are draft presentation code and
have no real record routes yet. Do not open Jinja templates with Live Server;
render them through Flask.

## Review the pages without a database

From this checkout, run:

```powershell
.\kind\Scripts\python.exe tools\preview_frontend.py
```

Open <http://127.0.0.1:5505/preview/> and choose a role. This review tool
renders the Jinja routes with a temporary in-memory test client, serves only
the rendered HTML and static assets on localhost, rejects POST requests and
does not create database tables. The role selector is only for design review;
normal Flask authentication and permissions are unchanged.

## Backend work to agree with the team

1. Rick supplies the agreed database schema and upgrade procedure. This
   frontend branch does not rebuild or migrate the local database.
2. Justin confirms the import scope, validation, duplicate rules and results,
   then connects the Workers import UI to the migration service.
3. Connect the registers, counts, scores, search and detail routes to
   tenant-scoped data. Show actual numbers only after the relevant queries work.
4. Add server-side validation and authorised POST routes for setup, worker and
   participant changes, notes, incidents, documents and uploads. Show success
   only after a real operation succeeds.

## Verification

```powershell
.\kind\Scripts\python.exe -m pytest -q
.\kind\Scripts\python.exe tools\preview_frontend.py --check
```

The frontend integration is developed on `jesse/frontend-workers` for team
review before it is merged into the shared project branch. The separate local
`start.ps1` change is not part of this frontend update.
