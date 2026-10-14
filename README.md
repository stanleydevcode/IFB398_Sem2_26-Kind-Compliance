# Kind Compliance Prototype Skeleton — Registration Version

This version starts with real registration/login instead of a seeded demo account.

## Frontend preview (no database required)

To review the integrated frontend pages while database work
is pending, run `.\kind\Scripts\python.exe tools\preview_frontend.py` from this
folder. Open <http://127.0.0.1:5505/preview/> and choose a preview role.
The review pages have no fictional records or saved data. Unconnected counts
are marked with a dash rather than a calculated result.
This static preview is separate from the normal Flask login workflow below.
See [frontend handoff](docs/frontend-handoff.md) for page ownership, permissions
and backend integration work.

## User flow

```text
Open site
  -> Login page
  -> Register
  -> Create organisation + first user
  -> First user becomes Organisation Administrator
  -> Organisation-specific tenant schema is created
  -> Organisation Setup
  -> Dashboard
```

Public registration does **not** let a user choose their own role. The first account for a newly created organisation becomes the Organisation Administrator. Compliance Manager and Staff Member accounts should later be created/invited by an Administrator.

## Stack

- Python 3.12
- Flask
- PostgreSQL 16
- SQLAlchemy
- Flask-Login
- Bootstrap 5
- Docker Compose for the local PostgreSQL database

## Recommended Windows location

Use the short path:

```text
C:\dev\kind-compliance
```

This avoids Windows long-path problems with Python packages.

## Run it

### 1. Start Docker Desktop, then PostgreSQL

```powershell
docker compose up -d
```

### 2. Create and activate Python 3.12 virtual environment

```powershell
py -3.12 -m venv kind
.\kind\Scripts\Activate.ps1
```

### 3. Install packages

```powershell
python -m pip install -r requirements.txt
```

### 4. Create `.env`

```powershell
Copy-Item .env.example .env
```

### 5. Create shared database tables

```powershell
python -m flask --app run.py init-db
```

### 6. Run the application

```powershell
python -m flask --app run.py run --debug
```

Open:

```text
http://127.0.0.1:5000
```

Choose **Register** and create your own organisation/admin account.

## Main modules

- Authentication / registration
- Dashboard
- Staff and credentials
- Documents and evidence
- Participants
- Incidents and complaints
- Risks
- Compliance requirements
- Organisation onboarding
- My Compliance
- Data migration

Most business modules are intentionally skeleton pages so different team members can build them independently.
