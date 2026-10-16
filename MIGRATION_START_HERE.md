# Install the data migration integration


In your existing `(kind)` PowerShell terminal:

```powershell
python -m flask --app run.py migration-init
python -m flask --app run.py migration-add-credential-type "First Aid"
python -m flask --app run.py migration-add-credential-type "CPR"
python -m flask --app run.py migration-add-credential-type "Worker Screening"
python -m flask --app run.py run --debug
```

Open <http://127.0.0.1:5000/migration/> as an Administrator or Compliance Manager.

Read [the migration README](docs/data-migration/README.md) for setup, examples, expected results, duplicate handling, documents and team integration boundaries. Begin with `examples/migration/history/01_staff_history.csv` and use `Legacy demo` as the source system for all related fixtures.
