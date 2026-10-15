"""Additive upgrade of existing tenant schemas; never drop tables/data."""
import click
from flask.cli import with_appcontext
from sqlalchemy import inspect, select

from app.extensions import db
from app.models import Organisation, CredentialType
from app.models.migration import (MigrationJob, MigrationRow, SourceIdentity,
                                  MigrationAttachment, MigrationChange)
from app.services.tenant import tenant_bind


@click.command("migration-init")
@click.option("--organisation-id", help="Limit the additive upgrade to one existing organisation.")
@with_appcontext
def migration_init(organisation_id):
    """Create migration tables in existing organisation schemas (idempotent)."""
    query = select(Organisation)
    if organisation_id:
        query = query.where(Organisation.id == organisation_id)
    organisations = db.session.scalars(query).all()
    if organisation_id and not organisations:
        raise click.ClickException("Organisation not found.")
    tables = [model.__table__ for model in (MigrationJob, MigrationRow, SourceIdentity,
                                          MigrationAttachment, MigrationChange)]
    for organisation in organisations:
        bind = tenant_bind(organisation.id)
        if not inspect(bind).has_table("staff", schema=organisation.schema_name):
            raise click.ClickException(f"Existing tenant schema missing for {organisation.id}; provision it first.")
        db.metadata.create_all(bind=bind, tables=tables)
        click.echo(f"Migration tables ready for {organisation.id}.")
    click.echo(f"Prepared {len(organisations)} existing organisation(s). New registrations include these tables automatically.")


@click.command("migration-add-credential-type")
@click.argument("name")
@click.option("--no-expiry", is_flag=True, help="This configured type does not require an expiry date.")
@with_appcontext
def add_credential_type(name, no_expiry):
    """Developer-managed shared catalogue; never inferred from an uploaded row."""
    from sqlalchemy import func
    name = name.strip()
    if not name or len(name) > 150:
        raise click.ClickException("Use a name between 1 and 150 characters.")
    existing = db.session.scalar(select(CredentialType).where(func.lower(CredentialType.name) == name.lower()))
    if existing:
        click.echo("Already configured; existing expiry rules preserved.")
        return
    db.session.add(CredentialType(name=name, has_expiry=not no_expiry))
    db.session.commit()
    click.echo(f"Configured credential type: {name}")


def register_migration_commands(app):
    app.cli.add_command(migration_init)
    app.cli.add_command(add_credential_type)
