# Connect imported records to the normal pages

Extract this overlay into your existing repository root beside run.py, after stopping Flask and backing up/committing your work. It includes the prior startup fix, so it can be applied directly to the latest merged ZIP uploaded in this conversation. Your .env, Docker configuration, requirements and database records are excluded.

Run:

```powershell
python -m flask --app run.py db-check
python -m flask --app run.py migration-init
python -m pytest -q
python -m flask --app run.py run --debug
```

Previously approved imports will appear automatically on Workers and Participants. Accepted documents appear in Documents; pending originals are under Awaiting sign-off. There is no need to re-import existing records.

Read docs/data-migration/CONNECTED_PAGES.md for profile edits, original uploads, document replacement, credential verification, account linking, assigned participant access, test steps and known limits. The full suite currently has 77 passing tests on SQLite test databases; PostgreSQL/browser checks still need to be run locally.
