"""Regression coverage for feedback issues 2 and 3."""
import re
from datetime import date

import pytest
from sqlalchemy import select, func

from app.models import Participant, Staff, StaffCredential, Case
from app.models.migration import MigrationChange, MigrationJob
from app.services.migration.engine import fingerprint
from app.services.tenant import tenant_session
from conftest import ORG_A, post
from test_workflow import stage, state, approve, review, staff_file, table


def open_review(client, job, row, target):
    """Capture the actual hidden fields from the page the reviewer opened."""
    url = f"/migration/{job}/rows/{row['id']}"
    html = client.get(url).get_data(as_text=True)
    payload = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)">', html))
    payload.update(decision='update', target_id=target, reason='Reviewed historical correction')
    payload.update({'field_' + key: value for key, value in row['data'].items()})
    return url, payload


def participant_import(client, **dates):
    values = dict(source_reference='P-01', first_name='Casey', last_name='Example', **dates)
    return stage(client, table(list(values), [list(values.values())]), 'participant')


@pytest.mark.parametrize('changes', [
    {'plan_end_date': '2026-01-01'},
    {'plan_start_date': '2028-10-01'},
])
def test_partial_plan_update_validates_retained_endpoint(application, client, changes):
    initial = participant_import(client, plan_start_date='2026-10-01', plan_end_date='2027-10-01')
    approve(client, initial, state(application, initial))
    target = state(application, initial)[0]['destination_id']
    update = participant_import(client, **changes)
    row = state(application, update)[0]
    assert review(client, update, row, decision='update', target_id=target,
                  reason='Review changed plan date').status_code == 302
    assert state(application, update)[0]['state'] == 'invalid'
    assert any('plan_end_date cannot precede plan_start_date' in error
               for error in state(application, update)[0]['errors'])
    assert approve(client, update, state(application, update)).status_code == 302
    with application.app_context(), tenant_session(ORG_A) as tenant:
        person = tenant.get(Participant, target)
        assert person.plan_start_date == date(2026, 10, 1)
        assert person.plan_end_date == date(2027, 10, 1)
        assert tenant.scalar(select(func.count()).select_from(MigrationChange)) == 0


def test_valid_partial_plan_update_preserves_unmapped_start(application, client):
    initial = participant_import(client, plan_start_date='2026-10-01', plan_end_date='2027-10-01')
    approve(client, initial, state(application, initial))
    target = state(application, initial)[0]['destination_id']
    update = participant_import(client, plan_end_date='2028-10-01')
    assert review(client, update, state(application, update)[0], decision='update', target_id=target,
                  reason='Reviewed extension').status_code == 302
    assert approve(client, update, state(application, update)).status_code == 302
    assert state(application, update)[0]['state'] == 'imported'
    with application.app_context(), tenant_session(ORG_A) as tenant:
        person = tenant.get(Participant, target)
        assert person.plan_start_date == date(2026, 10, 1)
        assert person.plan_end_date == date(2028, 10, 1)


def test_partial_credential_update_validates_retained_issue_date(application, client):
    staff = stage(client, staff_file())
    approve(client, staff, state(application, staff))
    initial = stage(client, table(['source_reference', 'staff_reference', 'credential_type', 'issue_date', 'expiry_date'],
        [['C-01', 'S-01', 'First Aid', '2026-01-01', '2027-01-01']]), 'credential')
    approve(client, initial, state(application, initial))
    target = state(application, initial)[0]['destination_id']
    update = stage(client, table(['source_reference', 'staff_reference', 'credential_type', 'expiry_date'],
        [['C-01', 'S-01', 'First Aid', '2025-01-01']]), 'credential')
    review(client, update, state(application, update)[0], decision='update', target_id=target,
           reason='Reviewed certificate correction')
    assert state(application, update)[0]['state'] == 'invalid'
    approve(client, update, state(application, update))
    with application.app_context(), tenant_session(ORG_A) as tenant:
        assert tenant.get(StaffCredential, target).expiry_date == date(2027, 1, 1)


@pytest.mark.parametrize('kind', ['incident', 'complaint'])
def test_case_update_validates_retained_closure_time(application, client, kind):
    values = dict(source_reference='CASE-01', category='historical', description='Historical example',
                  occurred_at='2025-01-01T09:00:00+10:00', reported_at='2025-01-02T09:00:00+10:00',
                  severity='low', status='closed', reportability='requires_review',
                  closed_at='2025-01-03T09:00:00+10:00', outcome='Historical resolution')
    initial = stage(client, table(list(values), [list(values.values())]), kind)
    approve(client, initial, state(application, initial))
    target = state(application, initial)[0]['destination_id']
    values.update(occurred_at='2025-01-04T09:00:00+10:00', reported_at='2025-01-05T09:00:00+10:00',
                  status='investigating', closed_at='', outcome='')
    update = stage(client, table(list(values), [list(values.values())]), kind)
    review(client, update, state(application, update)[0], decision='update', target_id=target,
           reason='Reviewed historical date correction')
    assert state(application, update)[0]['state'] == 'invalid'
    assert any('closed_at cannot precede occurred_at' in error for error in state(application, update)[0]['errors'])
    approve(client, update, state(application, update))
    with application.app_context(), tenant_session(ORG_A) as tenant:
        assert tenant.get(Case, target).status == 'closed'


def test_destination_changed_after_page_open_requires_fresh_review(application, client):
    initial = stage(client, staff_file())
    approve(client, initial, state(application, initial))
    target = state(application, initial)[0]['destination_id']
    update = stage(client, staff_file(first='Imported correction'))
    row = state(application, update)[0]
    url, old_form = open_review(client, update, row, target)
    with application.app_context(), tenant_session(ORG_A) as tenant:
        tenant.get(Staff, target).first_name = 'Newer saved name'
    response = post(client, url, old_form)
    assert response.status_code == 400
    assert b'Reload' in response.data
    approve(client, update, state(application, update))
    with application.app_context(), tenant_session(ORG_A) as tenant:
        assert tenant.get(Staff, target).first_name == 'Newer saved name'
        assert tenant.scalar(select(func.count()).select_from(MigrationChange)) == 0
    # Explicitly reload, inspect the new snapshot, and submit the decision again.
    url, new_form = open_review(client, update, state(application, update)[0], target)
    assert post(client, url, new_form).status_code == 302
    assert approve(client, update, state(application, update)).status_code == 302
    with application.app_context(), tenant_session(ORG_A) as tenant:
        assert tenant.get(Staff, target).first_name == 'Imported correction'


def test_previously_queued_invalid_partial_update_is_rechecked_at_approval(application, client):
    initial = participant_import(client, plan_start_date='2026-10-01', plan_end_date='2027-10-01')
    approve(client, initial, state(application, initial))
    target = state(application, initial)[0]['destination_id']
    update = participant_import(client, plan_end_date='2026-01-01')
    # Simulate an update already queued by the old implementation before deployment.
    with application.app_context(), tenant_session(ORG_A) as tenant:
        row = tenant.get(MigrationJob, update).rows[0]
        row.decision, row.target_id, row.decision_reason = 'update', target, 'Previously reviewed'
        row.target_snapshot = fingerprint(tenant.get(Participant, target))
        row.status = 'ready'
    assert approve(client, update, state(application, update)).status_code == 302
    assert state(application, update)[0]['state'] == 'invalid'
    with application.app_context(), tenant_session(ORG_A) as tenant:
        assert tenant.get(Participant, target).plan_end_date == date(2027, 10, 1)


@pytest.mark.parametrize('context_change', ['missing', 'tampered', 'other_row'])
def test_review_context_cannot_be_omitted_altered_or_reused(application, client, context_change):
    initial = stage(client, staff_file())
    approve(client, initial, state(application, initial))
    target = state(application, initial)[0]['destination_id']
    update = stage(client, staff_file(first='Imported correction'))
    row = state(application, update)[0]
    url, payload = open_review(client, update, row, target)
    if context_change == 'missing':
        payload.pop('review_token')
    elif context_change == 'tampered':
        payload['review_token'] += '-altered'
    else:
        other = stage(client, staff_file(first='Imported correction'))
        _, other_payload = open_review(client, other, state(application, other)[0], target)
        payload['review_token'] = other_payload['review_token']
    assert post(client, url, payload).status_code == 400
    assert state(application, update)[0]['decision'] == 'create'
    with application.app_context(), tenant_session(ORG_A) as tenant:
        assert tenant.get(Staff, target).first_name == 'Alex'
