# Restore the original frontend design

This cumulative overlay includes the connected Workers/Participants/Documents implementation and startup fix from this conversation, with layouts restored to the original Kind Compliance frontend design.

1. Stop Flask with Ctrl+C. Keep a commit/backup of your current branch.
2. Extract `Kind_Compliance_Design_Restored.zip`. Copy its contents into your existing repository root, beside `run.py`. Merge folders and replace the listed source files. Do not replace the repository with the ZIP.
3. Keep your existing `.env`, Docker configuration and database. Already approved imports remain visible without re-importing.
4. In your activated `(kind)` PowerShell terminal, run:

```powershell
python -m pytest -q
python -m flask --app run.py run --debug
```

If you have not applied the earlier migration-table setup, run `python -m flask --app run.py migration-init` before starting Flask. The design update itself adds no tables or dependencies.

Read [the update guide](docs/data-migration/DESIGN_RESTORATION.md) for changed pages, verification, merge notes and a browser checklist. Review and commit the changes on your data migration branch, then Push origin.
