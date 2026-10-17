# Frontend handoff

The current application keeps the original Kind Compliance visual system from the uploaded project: shared header/navigation, logo, IBM Plex Sans, teal actions, compact tables, tabs, counter strips, credential cards and two-column profiles. Original `theme.css` and `app.css` are unchanged. `records.css` extends that theme for working links/forms; migration styles are scoped to `.kc-migration`.

| Page | Current state |
| --- | --- |
| Workers | Live credential register, pending verification and Administrator login-link tabs. Working import links replace the old preview import modal. |
| Worker profile | Credential cards, originals/history, contact sidebar, editing and Compliance Manager verification. |
| Participants | Live register and authorised existing-note list. Assigned staff see only assigned participants/notes. |
| Participant profile | Care, notes, plan details, consent/sidebar, support team and authorised original files. |
| Documents | Original Library/Missing/Awaiting sign-off/Evidence tab design. Accepted library, sign-off queue, upload/replacement/download work. Missing assessment remains unassessed. |
| Dashboard | Original score/counter layout and 8/4 task/expiry columns, populated with live records. Scores remain unassessed. |
| My compliance | Original counter strip and main/sidebar layout, linked credentials, own originals and assigned participants. |
| Migration | Working import/review flows styled with the shared theme. |
| Organisation setup, incidents and risks | Existing prototype/workflow scope remains; see module implementation before presenting saves as available. |

No fictional business records are injected into the running application. Import approval, document sign-off and credential verification remain separate operations. Previously approved records need no re-import after a visual update.

## Review

Run `python tools/preview_frontend.py --check` to render static empty-state pages using disposable SQLite preview tables. `python tools/preview_frontend.py` serves them on http://127.0.0.1:5505/preview/. The server rejects POST requests; its preview-role selector is not production authentication. To test imports, edits, files and access controls, use the real Flask application and [connected-page walkthrough](data-migration/CONNECTED_PAGES.md).

Run `python -m pytest -q` for the regression suite. Check desktop/mobile layouts in your browser before merging. New controls should use existing `kc-*` components and authorised tenant-scoped endpoints. Do not reconnect obsolete preview JavaScript to the working record forms.
