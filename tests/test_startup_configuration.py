"""Factory regression tests: settings must be evaluated after dotenv loading."""
import os

from sqlalchemy import make_url

import app as app_package
from app import create_app
from app.extensions import db


def test_factory_reads_values_loaded_after_config_import(monkeypatch):
    # app/config.py has already been imported during test collection.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    def late_dotenv(*args, **kwargs):
        monkeypatch.setenv("DATABASE_URL", "sqlite://")
        monkeypatch.setenv("SECRET_KEY", "loaded-at-factory-time")
    monkeypatch.setattr(app_package, "load_dotenv", late_dotenv)
    application = create_app()
    assert application.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    assert application.config["SECRET_KEY"] == "loaded-at-factory-time"
    with application.app_context():
        db.engine.dispose()


def test_env_file_loads_from_project_path_and_preserves_process_override(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgresql+psycopg://kind:kind@127.0.0.1:5433/kind_compliance\nSECRET_KEY=fixture-key\n")
    monkeypatch.setattr(app_package, "ENV_FILE", env_file, raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    application = create_app()
    assert make_url(application.config["SQLALCHEMY_DATABASE_URI"]).port == 5433
    with application.app_context():
        db.engine.dispose()
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    another = create_app()
    assert another.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    with another.app_context():
        db.engine.dispose()


def test_custom_config_remains_authoritative(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://kind:kind@127.0.0.1:5433/kind_compliance")
    class ExplicitConfig:
        TESTING = True
        SECRET_KEY = "explicit-test-key"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
    application = create_app(ExplicitConfig)
    assert application.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"
    assert application.config["SECRET_KEY"] == "explicit-test-key"
    with application.app_context():
        db.engine.dispose()


def test_db_check_is_read_only_and_reports_success():
    from sqlalchemy import inspect
    class Local:
        TESTING = True
        SECRET_KEY = "check-test-only"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
    application = create_app(Local)
    result = application.test_cli_runner().invoke(args=["db-check"])
    assert result.exit_code == 0, result.output
    assert "Database connection successful" in result.output
    with application.app_context():
        assert inspect(db.engine).get_table_names() == []
        db.engine.dispose()


def test_db_check_warns_about_override_without_printing_secrets(monkeypatch):
    import dotenv
    monkeypatch.setattr(dotenv, "dotenv_values", lambda *a, **k: {
        "DATABASE_URL": "postgresql+psycopg://kind:DO-NOT-PRINT-THIS@127.0.0.1:5433/kind_compliance"})
    class Local:
        TESTING = True
        SECRET_KEY = "check-test-only"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
    application = create_app(Local)
    result = application.test_cli_runner().invoke(args=["db-check"])
    assert result.exit_code == 0
    assert "differs from the project .env" in result.output
    assert "DO-NOT-PRINT-THIS" not in result.output
    with application.app_context():
        db.engine.dispose()


def test_db_check_failure_has_clear_error_without_connection_details(monkeypatch):
    from sqlalchemy.exc import OperationalError
    class Local:
        TESTING = True
        SECRET_KEY = "check-test-only"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
    application = create_app(Local)
    with application.app_context():
        def fail():
            raise OperationalError("sensitive SQL", None, Exception("DO-NOT-PRINT-THIS"))
        monkeypatch.setattr(db.engine, "connect", fail)
        result = application.test_cli_runner().invoke(args=["db-check"])
        assert result.exit_code != 0
        assert "Database connection failed" in result.output
        assert "DO-NOT-PRINT-THIS" not in result.output
        assert "sensitive SQL" not in result.output
        db.engine.dispose()
