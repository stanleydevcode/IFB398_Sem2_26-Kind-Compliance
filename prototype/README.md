# Kind Compliance — hi-fi prototype / front end

Flask + Jinja templates with sample data. The same templates become the real front end
once `data.py` is swapped for PostgreSQL queries.

    pip install -r requirements.txt
    python app.py          # http://localhost:5000  (pick a role on the sign-in screen)
    python freeze.py       # static export to ./build (hosting + Figma import)

## Files
- `app.py`        routes; every page sits under its role, e.g. `/admin/dashboard.html`
- `data.py`       sample organisation (Brightwater Care, demo date 27 Sep 2026) and the business rules:
                  task priority, risk escalation, missing documents from registration groups,
                  expiry bands, dashboard counters and health score
- `freeze.py`     lists every page for the static export
- `templates/`    `base_app.html` + `partials/` (header, modals) and one template per screen
- `static/css/theme.css`  design tokens (palette, status colours, 6px radius) and components
- `static/js/kc.js`       shared behaviour: toasts, global search, countdown timers

## Screens
| Screen | Administrator | Compliance Manager | Staff Member |
|---|---|---|---|
| Sign in | ✓ | ✓ | ✓ |
| Dashboard | ✓ | ✓ | — |
| Documents (+ document page) | ✓ | ✓ | — |
| Workers (+ worker page, "View as") | ✓ | ✓ | — |
| Participants (+ profile) | ✓ | ✓ | own participants |
| Incidents (+ report form, case page) | ✓ | ✓ | own reports |
| My compliance | right of menu bar | right of menu bar | home page |
| Organisation setup | ✓ | — | — |

Buttons show a confirmation message but nothing is saved yet (no database).
The setup "Finish" state lasts for the browser session so the demo can be repeated.

## Design decisions
- White background, teal as the product colour (Glassdoor palette, chosen by Mikela).
  The plum is only used in the logo.
- Red, amber and green are only used for status. Good states ("Valid", "Current") are plain text
  so problems stand out.
- Corners are 6px. Main buttons are flat; only the sign-in button has the soft teal glow.
- Dashboard order: urgent alerts, scores, counters, then "What to do next" as the main column.
  The two score cards were cut down to one strip because they took too much space.
- Lists are sorted by what needs attention: workers by soonest expiry, cases with overdue
  actions first, and Documents opens on "Missing" when documents are missing.
- Task priority follows Mikela's rule: severity first, then days overdue.
- For Administrator and Compliance Manager, My compliance sits on the right of the menu bar, apart
  from the organisation tabs, with a dot when something on their own record needs attention.
  For Staff Members it is the home page.
