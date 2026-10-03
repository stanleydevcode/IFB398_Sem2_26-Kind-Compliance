import click
from flask.cli import with_appcontext

from app.extensions import db


def register_commands(app):
    app.cli.add_command(init_db)


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
    click.echo("Created shared/public database tables.")
