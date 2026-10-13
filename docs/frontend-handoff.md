# Workers frontend handoff

## Where to edit

| File | Prototype reference | Responsibility |
| --- | --- | --- |
| `app/templates/base.html` | Header and navigation shared by the prototype pages | Shared layout, real account menu, flash messages and template blocks |
| `app/templates/staff/index.html` | `admin/workers.html` and `manager/workers.html` | Workers register, verification/access tabs, Add worker form and Import modal |
| `app/static/js/workers.js` | Workers page interactions | Tabs, filters, file selection and example import decisions |
| `app/services/ui.py` | Role-specific prototype navigation | Presentation context from the existing signed-in membership |

The existing URL remains `/staff/`. Flask renders the Jinja template; do not open
the template with Live Server. Sign in to the running app and choose **Workers**.

The prototype's theme, IBM Plex Sans fonts, Bootstrap, Bootstrap Icons and images
are copied into `app/static/`. Keep the theme shared when building other pages.
Pages can extend `base.html` and use its `title`, `content`, `head` and `scripts`
blocks. Existing templates still use the same `title` and `content` blocks.

## Implemented now

- Prototype layout with an empty Workers register and zero counters.
- Register, Awaiting verification, and administrator-only Logins & access tabs.
- Administrator-only Import modal with CSV/Excel selection and an explicitly
  labelled example preview matching the prototype's two problem rows.
- Example decisions update the selected count: both rows skipped means 10;
  both included means 12. Cancel/reopen resets the example.
- Add worker form layout; saving, exporting and actual importing stay disabled.

## Integration still needed

- Rick/Justin agree on migration entities, final columns, required fields and
  duplicate rules before publishing a real import template.
- Justin connects uploaded-file validation, real previews and confirmed imports.
  Selecting a local file currently shows its name; it does not parse/upload it.
- Connect register rows, counters, renewals and login access to real records.
- Connect Add worker and Export; replace preview notices only when those actions
  really save/export data. Worker detail pages are a subsequent task.
- Search currently finds available pages. Record search and notifications need
  real data, so prototype people/alerts are not presented as actual records.

## Compatibility

Authentication, POST logout, roles, database models, tenant provisioning and the
existing migration service are retained. The staff route keeps its existing
login and manager permission decorators. No database records are changed by this
frontend work. Original edited files are backed up under the ignored local
`.tmp-kind/before-frontend/` folder.

Run checks from the project root:

```powershell
.\kind\Scripts\python.exe -m pytest -q
```

Original skeleton tests and frontend permission/form rendering checks pass.
