import click
from flask.cli import with_appcontext

from app.extensions import db
from app.constants import ALL_ROLES
from app.models.identity import Role


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
    for role_name in sorted(ALL_ROLES):
        if Role.query.filter_by(name=role_name).first() is None:
            db.session.add(Role(name=role_name))
    db.session.commit()
    click.echo("Created shared/public database tables.")
