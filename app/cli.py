import click
from flask.cli import with_appcontext

from app.extensions import db
from app.constants import ALL_ROLES
from app.models.identity import Role


def register_commands(app):
    app.cli.add_command(init_db)
    app.cli.add_command(check_database)
    from app.services.migration.commands import register_migration_commands
    register_migration_commands(app)


@click.command("init-db")
@with_appcontext
def init_db():
    # Create only the shared/public tables here.
    # Organisation-specific tenant tables are created during registration.
    public_tables = [
        table
        for table in db.metadata.tables.values()
        if table.schema == "public"
    ]

    db.metadata.create_all(bind=db.engine, tables=public_tables)
    for role_name in sorted(ALL_ROLES):
        if Role.query.filter_by(name=role_name).first() is None:
            db.session.add(Role(name=role_name))
    db.session.commit()
    click.echo("Created shared/public database tables.")


@click.command("db-check")
@with_appcontext
def check_database():
    """Show the selected endpoint (no credentials) and check the connection."""
    from pathlib import Path
    from dotenv import dotenv_values
    from flask import current_app
    from sqlalchemy import make_url, text
    from sqlalchemy.exc import SQLAlchemyError

    endpoint = db.engine.url
    click.echo(f"Database endpoint: {endpoint.host or 'local'}:{endpoint.port or 'default'} / {endpoint.database or 'memory'}")
    env_file = Path(current_app.root_path).parent / ".env"
    file_url = dotenv_values(env_file, encoding="utf-8-sig").get("DATABASE_URL")
    if file_url:
        try:
            different = make_url(file_url) != endpoint
        except (ValueError, SQLAlchemyError):
            different = True
        if different:
            click.echo("Notice: the selected connection differs from the project .env. An existing DATABASE_URL environment variable or explicit app configuration can override that file.")
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise click.ClickException("Database connection failed. Check the endpoint above, Docker's published port and the database credentials. No tables were changed.") from None
    click.echo("Database connection successful. No tables were changed.")
