import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, configure_mappers

from app import models
from app.extensions import db


def test_erd_models_are_registered():
    expected = {'roles', 'practice_modules', 'registration_group_modules',
                'service_agreements', 'form_templates', 'form_submissions',
                'risk_controls', 'participant_consents', 'cases'}
    assert expected <= {table.name for table in db.metadata.tables.values()}
    assert hasattr(models, 'ParticipantConsent')
    assert hasattr(models, 'Case')


def test_every_erd_foreign_key_resolves():
    expected = {
        'public.memberships': {'role_id': 'public.roles.id'},
        'tenant.staff': {'user_id': 'public.users.id'},
        'tenant.documents': {'document_type_code': 'public.document_types.code',
                             'compliance_area_code': 'public.compliance_areas.code',
                             'current_version_id': 'tenant.document_versions.id'},
        'tenant.evidence_links': {'organisation_requirement_id': 'tenant.organisation_requirements.id',
                                  'form_submission_id': 'tenant.form_submissions.id',
                                  'reviewed_by': 'public.users.id'},
        'tenant.cases': {'assigned_membership_id': 'public.memberships.id',
                         'participant_id': 'tenant.participants.id',
                         'reported_by_staff_id': 'tenant.staff.id'},
        'tenant.corrective_actions': {'case_id': 'tenant.cases.id',
                                      'risk_id': 'tenant.risks.id'},
    }
    for name, fks in expected.items():
        table = db.metadata.tables.get(name)
        assert table is not None, name
        for column, target in fks.items():
            assert column in table.c, (name, column)
            assert {fk.target_fullname for fk in table.c[column].foreign_keys} == {target}
    for table in db.metadata.tables.values():
        for fk in table.foreign_keys:
            assert fk.column is not None
    configure_mappers()


def test_risk_scores_are_integer():
    from sqlalchemy import Integer
    assert isinstance(models.Risk.__table__.c.likelihood.type, Integer)
    assert isinstance(models.Risk.__table__.c.consequence.type, Integer)


@pytest.fixture
def session():
    engine = create_engine('sqlite://', execution_options={
        'schema_translate_map': {'public': None, 'tenant': None}})
    @event.listens_for(engine, 'connect')
    def foreign_keys(conn, _):
        conn.execute('PRAGMA foreign_keys=ON')
    db.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_document_current_version_and_form_evidence_round_trip(session):
    from app.models.documents import Document, DocumentVersion, EvidenceLink
    from app.models.organisation import OrganisationRequirement
    from app.models.reference import ComplianceArea, ComplianceRequirement
    area = ComplianceArea(code='core', name='Core')
    requirement = ComplianceRequirement(name='Policy', compliance_area=area)
    org_requirement = OrganisationRequirement(requirement=requirement)
    user = models.User(email='reviewer@example.com', password_hash='hash')
    doc = Document(title='Policy')
    version = DocumentVersion(document=doc, version_no=1, file_path='policy.pdf', uploader=user)
    doc.current_version = version
    template = models.FormTemplate(name='Review', form_type='review', schema_definition={})
    submission = models.FormSubmission(template=template, submitter=user, data={'ok': True})
    evidence = EvidenceLink(organisation_requirement=org_requirement,
                            form_submission=submission, reviewer=user)
    session.add_all([doc, evidence])
    session.commit()
    session.expire_all()
    loaded = session.get(Document, doc.id)
    assert loaded.current_version.document_id == loaded.id
    assert loaded.versions[0].file_path == 'policy.pdf'
    assert session.get(EvidenceLink, evidence.id).form_submission.data == {'ok': True}
    assert evidence.document_id is None


def test_role_and_tenant_schema_defaults(session):
    organisation = models.Organisation(legal_name='Provider')
    user = models.User(email='admin@example.com', password_hash='hash')
    role = models.Role(name='organisation_admin')
    membership = models.Membership(organisation=organisation, user=user, role_record=role)
    session.add(membership)
    session.commit()
    assert membership.role == 'organisation_admin'
    assert organisation.schema_name.startswith('org_')
    assert organisation.is_active
    assert user.is_active
    user.is_active_account = False
    assert user.is_active is False


def test_case_risk_and_action_relationships(session):
    staff = models.Staff(first_name='A', last_name='Worker', email='worker@example.com')
    participant = models.Participant(first_name='B', last_name='Participant', key_worker=staff)
    case = models.Case(case_type='incident', category='injury', description='Fall',
                       participant=participant, reporter=staff)
    risk = models.Risk(title='Falls', likelihood=2, consequence=3, owner=staff)
    control = models.RiskControl(risk=risk, description='Hand rail', control_type='preventive')
    action = models.CorrectiveAction(case=case, risk=risk, description='Install rail')
    session.add_all([control, action])
    session.commit()
    session.expire_all()
    assert action.case.participant.key_worker.id == staff.id
    assert action.risk.controls[0].description == 'Hand rail'
    assert models.IncidentCase is models.Case


def test_public_roles_are_seeded_once_and_registration_reuses_them(monkeypatch):
    from app import create_app
    from app.constants import ALL_ROLES
    from app.blueprints.auth import routes

    class Config:
        TESTING = True
        SECRET_KEY = 'test'
        SQLALCHEMY_DATABASE_URI = 'sqlite://'
        SQLALCHEMY_ENGINE_OPTIONS = {
            'execution_options': {'schema_translate_map': {'public': None, 'tenant': None}},
        }

    app = create_app(Config)
    provisioned = []
    # SQLite cannot create PostgreSQL schemas; the ORM uses translated tables.
    monkeypatch.setattr(routes, 'provision_tenant_schema', provisioned.append)
    runner = app.test_cli_runner()
    assert runner.invoke(args=['init-db']).exit_code == 0
    assert runner.invoke(args=['init-db']).exit_code == 0
    client = app.test_client()
    for index in range(2):
        response = client.post('/auth/register', data={
            'organisation_name': f'Provider {index}',
            'email': f'admin{index}@example.com',
            'password': 'password123', 'confirm_password': 'password123',
        })
        assert response.status_code == 302
        assert response.location.endswith('/onboarding/')
        assert client.get('/onboarding/').status_code == 200
        assert client.get('/').status_code == 200
        client.post('/auth/logout')
        response = client.post('/auth/login', data={
            'email': f'admin{index}@example.com', 'password': 'password123',
        })
        assert response.status_code == 302
        assert client.get('/onboarding/').status_code == 200
        client.post('/auth/logout')
    with app.app_context():
        assert {role.name for role in models.Role.query.all()} == ALL_ROLES
        memberships = models.Membership.query.all()
        assert len(memberships) == 2
        assert memberships[0].role_id == memberships[1].role_id
        assert len(provisioned) == 2
        assert models.Membership.query.filter_by(role='organisation_admin').count() == 2


@pytest.mark.parametrize('kind', ['participant', 'staff', 'document', 'organisation', 'user'])
def test_owned_records_follow_parent_delete_cascades(session, kind):
    if kind == 'participant':
        parent = models.Participant(first_name='A', last_name='B')
        children = [models.ParticipantConsent(participant=parent, consent_type='collect'),
                    models.ParticipantNote(participant=parent,
                        staff=models.Staff(first_name='C', last_name='D'),
                        note_type='care', content='Note')]
    elif kind == 'staff':
        parent = models.Staff(first_name='A', last_name='B')
        children = [models.StaffCredential(staff=parent,
                    credential_type=models.CredentialType(name='First aid'))]
    elif kind == 'document':
        parent = models.Document(title='Policy')
        version = models.DocumentVersion(document=parent, version_no=1, file_path='policy.pdf',
                    uploader=models.User(email='uploader@example.com', password_hash='hash'))
        parent.current_version = version
        children = [version]
    else:
        organisation = models.Organisation(legal_name='Provider')
        user = models.User(email='member@example.com', password_hash='hash')
        parent = organisation if kind == 'organisation' else user
        children = [models.Membership(organisation=organisation, user=user,
                    role_record=models.Role(name='staff_member'))]
    session.add_all([parent, *children])
    session.commit()
    identifiers = [(type(child), child.id) for child in children]
    session.delete(parent)
    session.commit()
    for child_type, child_id in identifiers:
        assert session.get(child_type, child_id) is None
