"""Restored register tabs retain the existing tenant and assignment boundaries."""
from sqlalchemy import select

from app.models import Participant, ParticipantNote, StaffCredential
from app.services.tenant import tenant_session
from conftest import ORG_A, ORG_B, login
from test_connected_pages import setup_people, staff_payload, normal_post
from test_workflow import stage, table, approve, state


def test_notes_tab_uses_authorised_participants_and_search(application, client):
    staff_id, person_id = setup_people(application, client)
    normal_post(client, f'/staff/{staff_id}/edit', staff_payload(
        application, staff_id, user_id=application.test_users['staff']))
    with application.app_context(), tenant_session(ORG_A) as tenant:
        other = Participant(first_name='Private', last_name='Other')
        tenant.add(other)
        tenant.flush()
        tenant.add_all([
            ParticipantNote(participant_id=person_id, staff_id=staff_id,
                            note_type='progress', content='Assigned participant note'),
            ParticipantNote(participant_id=other.id, staff_id=staff_id,
                            note_type='handover', content='Unassigned confidential note'),
        ])
    staff = login(application, 'staff', ORG_A)
    html = staff.get('/participants/assigned?tab=notes').get_data(as_text=True)
    assert 'Assigned participant note' in html
    assert 'Unassigned confidential note' not in html
    assert b'Assigned participant note' not in staff.get(
        '/participants/assigned?tab=notes&q=NoMatch').data
    manager_html = client.get('/participants/?tab=notes').get_data(as_text=True)
    assert 'Assigned participant note' in manager_html and 'Unassigned confidential note' in manager_html
    assert b'Assigned participant note' not in login(application, 'admin_b', ORG_B).get(
        '/participants/?tab=notes').data


def test_worker_verification_queue_and_login_tab_permissions(application, client):
    staff_id, _ = setup_people(application, client)
    job = stage(client, table(['source_reference', 'staff_reference', 'credential_type', 'expiry_date'],
                             [['C-TAB', 'S-01', 'First Aid', '2027-08-31']]), 'credential')
    approve(client, job, state(application, job))
    queue = client.get('/staff/?tab=verify')
    assert queue.status_code == 200
    assert b'2027-08-31' in queue.data and f'/staff/{staff_id}'.encode() in queue.data
    assert client.get('/staff/?tab=logins').status_code == 200
    assert login(application, 'manager', ORG_A).get('/staff/?tab=logins').status_code == 403
    assert login(application, 'staff', ORG_A).get('/staff/?tab=verify').status_code == 403
    with application.app_context(), tenant_session(ORG_A) as tenant:
        tenant.scalar(select(StaffCredential)).status = 'verified'
    assert b'2027-08-31' not in client.get('/staff/?tab=verify').data
    assert client.get('/staff/?tab=invalid').status_code == 400
    assert client.get('/participants/?tab=invalid').status_code == 400
