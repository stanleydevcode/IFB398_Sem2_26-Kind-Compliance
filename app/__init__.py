from flask import Flask
from dotenv import load_dotenv
from pathlib import Path

from app.config import Config
from app.extensions import db, login_manager, migrate

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def create_app(config_object=None):
    # Respect an explicit process/deployment override; otherwise use this project's file.
    load_dotenv(ENV_FILE, override=False, encoding="utf-8-sig")

    app = Flask(__name__)
    if config_object is None:
        app.config.from_mapping(Config.from_environment())
    else:
        app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Import models so SQLAlchemy knows about all tables.
    from app import models  # noqa: F401

    # Register blueprints.
    from app.blueprints.auth.routes import bp as auth_bp
    from app.blueprints.dashboard.routes import bp as dashboard_bp
    from app.blueprints.staff.routes import bp as staff_bp
    from app.blueprints.documents.routes import bp as documents_bp
    from app.blueprints.participants.routes import bp as participants_bp
    from app.blueprints.incidents.routes import bp as incidents_bp
    from app.blueprints.risks.routes import bp as risks_bp
    from app.blueprints.compliance.routes import bp as compliance_bp
    from app.blueprints.onboarding.routes import bp as onboarding_bp
    from app.blueprints.my_compliance.routes import bp as my_compliance_bp
    from app.blueprints.migration.routes import bp as migration_bp

    for blueprint in (
        auth_bp,
        dashboard_bp,
        staff_bp,
        documents_bp,
        participants_bp,
        incidents_bp,
        risks_bp,
        compliance_bp,
        onboarding_bp,
        my_compliance_bp,
        migration_bp,
    ):
        app.register_blueprint(blueprint)

    from app.cli import register_commands
    register_commands(app)

    from app.services.ui import shell_context
    app.context_processor(shell_context)

    return app
