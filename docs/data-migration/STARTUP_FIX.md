# Database endpoint and startup fix

Review of the merged project uploaded on 15 October 2026:

- All 59 migration integration package files are present and unchanged.
- Docker exposes PostgreSQL on computer port 5433; its internal port is 5432.
- Both the uploaded .env and .env.example select localhost:5433.
- The attached error log instead shows the app connecting to 127.0.0.1:5432.
- All 63 existing tests pass on the merged project using the SQLite test backends.

The log does not reveal the active terminal environment, so it cannot prove exactly why 5432 was selected. A previously set DATABASE_URL is a likely cause because environment variables take precedence over .env. The log could also predate the current configuration files. No password/database reset is needed to correct this endpoint mismatch.

A separate startup bug was reproduced: Config read the environment at module import, before create_app loaded .env. This can select the fallback port when creating the app outside Flask's CLI, which normally loads dotenv before importing the app. The fix loads this project's .env explicitly, then reads runtime settings. It preserves deliberate process environment overrides and explicit test configurations.

## Apply the small patch

Stop Flask and extract this ZIP into the existing repository root beside run.py. It replaces only:

- app/__init__.py
- app/config.py
- app/cli.py

It adds this guide and tests/test_startup_configuration.py. The migration implementation is unchanged. It contains no .env, Docker configuration, Git metadata, virtual environment or provider data.

## Start from the correct connection

In the existing (kind) PowerShell terminal at the repository root:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://kind:kind@127.0.0.1:5433/kind_compliance"
docker compose up -d
python -m flask --app run.py db-check
```

The new db-check command should print the endpoint with port 5433 and then:

```text
Database connection successful. No tables were changed.
```

A notice that the selected connection differs from .env is expected if the terminal uses 127.0.0.1 and the file uses localhost. To remove that cosmetic difference, use the same host spelling in both. Credentials are never printed by db-check.

If db-check fails, stop and inspect the reported endpoint and Docker mapping. To test credentials directly inside this project's container without changing data:

```powershell
docker compose exec -e PGPASSWORD=kind db psql -h 127.0.0.1 -U kind -d kind_compliance -c "SELECT 1;"
docker compose ps
```

The password above is the supplied project's local development default. Use the actual local configuration if you changed it. Do not delete Docker volumes or reset accounts just because the app selected a different port.

After a successful db-check, run these commands one at a time, stopping if one fails:

```powershell
python -m flask --app run.py init-db
python -m flask --app run.py migration-init
python -m flask --app run.py migration-add-credential-type "First Aid"
python -m flask --app run.py migration-add-credential-type "CPR"
python -m flask --app run.py migration-add-credential-type "Worker Screening"
python -m flask --app run.py run --debug
```

Open http://127.0.0.1:5000/migration/ as an Administrator or Compliance Manager. Confirm the workspace opens, then test the fictional staff CSV and dependent fixtures described in the migration README.

## Future terminals

Keep DATABASE_URL in the project's .env on port 5433. Do not copy .env.example over a configured .env during normal startup.

To use the .env value instead of an intentional temporary override, remove the current process variable before launching Flask:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m flask --app run.py db-check
```

If a new terminal keeps inheriting a different DATABASE_URL from Windows, inspect that user/system setting before changing it, since another project may rely on it. This patch intentionally respects deployment overrides rather than forcing a global port.

## Verification

All 69 tests pass after the patch: 63 existing tests plus six startup/configuration diagnostic tests. The new tests reproduced the original factory problem before the fix and check runtime dotenv loading, explicit-config precedence, read-only connection checks and credential-safe diagnostics.

The user's PostgreSQL instance cannot be accessed from this environment; a successful db-check on that computer is still required. Passing SQLite route/service tests does not establish a complete live PostgreSQL/browser deployment. The subsequent connected-page update now populates Workers, Participants, Documents, My compliance and dashboard counts. Its workflow and remaining incident/risk screen limits are documented in CONNECTED_PAGES.md.
