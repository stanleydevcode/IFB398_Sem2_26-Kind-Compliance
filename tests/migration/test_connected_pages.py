"""Approved imports feed normal pages; assignments scope all direct file routes."""
import io
import re
from datetime import date

from sqlalchemy import select, func

from app.models import (Staff, Participant, StaffCredential, Document, DocumentVersion, AuditLog,
                        ParticipantConsent, ParticipantNote)
from app.models.migration import SourceIdentity
from app.services.tenant import tenant_session
from app.services.migration.engine import fingerprint
from app.services import record_pages
from conftest import ORG_A, ORG_B, login
from test_workflow import stage, state, approve, staff_file, table


def normal_post(client,url,data=None,**kwargs):
    with client.session_transaction() as session:
        session['records_csrf']='record-test-csrf'
    payload=dict(data or {});payload['csrf_token']='record-test-csrf'
    return client.post(url,data=payload,**kwargs)


def staff_payload(app,staff_id,**changes):
    with app.app_context(),tenant_session(ORG_A) as s:
        worker=s.get(Staff,staff_id)
        result={k:getattr(worker,k) or '' for k in ['first_name','last_name','email','phone','job_title','employment_type']}
        result.update(start_date=str(worker.start_date or ''),is_active='yes' if worker.is_active else 'no',
                      user_id=worker.user_id or '',revision=fingerprint(worker),reason='Reviewed profile correction')
    result.update(changes);return result


def participant_payload(app,person_id,**changes):
    with app.app_context(),tenant_session(ORG_A) as s:
        person=s.get(Participant,person_id)
        result={k:getattr(person,k) or '' for k in ['first_name','last_name','ndis_number','support_type','plan_status',
            'emergency_contact_name','emergency_contact_phone','care_requirements']}
        result.update({k:str(getattr(person,k) or '') for k in ['date_of_birth','plan_start_date','plan_end_date']})
        result.update(key_worker_staff_id=person.key_worker_staff_id or '',revision=fingerprint(person),reason='Reviewed assignment/profile')
    result.update(changes);return result


def setup_people(app,client):
    job=stage(client,staff_file());approve(client,job,state(app,job));staff_id=state(app,job)[0]['destination_id']
    job=stage(client,table(['source_reference','first_name','last_name','key_worker_reference','care_requirements'],
        [['P-01','Casey','Example','S-01','Sensitive assigned care description']]),'participant')
    approve(client,job,state(app,job));person_id=state(app,job)[0]['destination_id']
    return staff_id,person_id


def upload_document(client,**changes):
    payload={'title':'Linked evidence','document_kind':'consent','review_date':'2027-01-01',**changes}
    payload['file']=(io.BytesIO(b'%PDF-1.4\nFictional protected original\n'),'original.pdf')
    response=normal_post(client,'/documents/upload',payload,content_type='multipart/form-data')
    assert response.status_code==302,response.get_data(as_text=True)
    return response.location.rsplit('/',1)[-1]


def version_for(app,document_id,number=1):
    with app.app_context(),tenant_session(ORG_A) as s:
        return s.scalar(select(DocumentVersion.id).where(DocumentVersion.document_id==document_id,DocumentVersion.version_no==number))


def accept_document(app,client,document_id,version_id=None):
    version_id=version_id or version_for(app,document_id)
    return normal_post(client,f'/documents/{document_id}/versions/{version_id}/review',
                       {'decision':'approved','notes':'Original and metadata reviewed','signoff':'yes'})


def test_staged_rows_absent_and_approved_imports_visible_on_normal_pages(application,client):
    job=stage(client,staff_file())
    assert b'worker@example.test' not in client.get('/staff/').data
    approve(client,job,state(application,job))
    staff_id=state(application,job)[0]['destination_id']
    html=client.get('/staff/').get_data(as_text=True)
    assert 'worker@example.test' in html and f'/staff/{staff_id}' in html
    assert client.get(f'/staff/{staff_id}').status_code==200
    assert client.get(f'/staff/{staff_id}/edit').status_code==200
    job=stage(client,table(['source_reference','first_name','last_name','key_worker_reference'],
                         [['P-01','Casey','Example','S-01']]),'participant')
    assert b'Casey' not in client.get('/participants/').data
    approve(client,job,state(application,job))
    person_id=state(application,job)[0]['destination_id']
    assert b'Casey' in client.get('/participants/').data
    assert client.get(f'/participants/{person_id}').status_code==200
    assert client.get(f'/participants/{person_id}/edit').status_code==200
    dashboard=client.get('/').get_data(as_text=True)
    assert '<b>1</b><span>Workers recorded' in dashboard
    assert '<b>1</b><span>Participants recorded' in dashboard
    assert 'Not assessed' in dashboard


def test_profile_edits_keep_identity_and_provenance_and_enforce_revision(application,client):
    staff_id,person_id=setup_people(application,client)
    stale=staff_payload(application,staff_id,phone='TEST-NEW-PHONE')
    response=normal_post(client,f'/staff/{staff_id}/edit',staff_payload(application,staff_id,job_title='Senior support worker'))
    assert response.status_code==302
    assert normal_post(client,f'/staff/{staff_id}/edit',stale).status_code==400
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(Staff,staff_id).job_title=='Senior support worker'
        assert s.scalar(select(SourceIdentity).where(SourceIdentity.entity_type=='staff')).destination_id==staff_id
    assert b'Senior support worker' in client.get(f'/staff/{staff_id}').data
    # Administrators retain the team's existing restriction on care edits.
    result=normal_post(client,f'/participants/{person_id}/edit',participant_payload(application,person_id,care_requirements='Unauthorised care rewrite'))
    assert result.status_code==403
    manager=login(application,'manager',ORG_A)
    result=normal_post(manager,f'/participants/{person_id}/edit',participant_payload(application,person_id,care_requirements='Reviewed care update'))
    assert result.status_code==302
    assert b'Reviewed care update' in client.get(f'/participants/{person_id}').data
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.scalar(select(SourceIdentity).where(SourceIdentity.entity_type=='participant')).destination_id==person_id
        assert s.scalar(select(AuditLog).where(AuditLog.action=='participant.updated')) is not None


def test_document_library_pending_replacements_downloads_and_dashboard(application,client):
    document=upload_document(client,title='Historical policy')
    version=version_for(application,document)
    assert b'Historical policy' not in client.get('/documents/').data
    assert b'Historical policy' in client.get('/documents/?tab=pending').data
    assert client.get(f'/documents/{document}').status_code==200
    assert accept_document(application,client,document).status_code==302
    assert b'Historical policy' in client.get('/documents/').data
    assert '<b>1</b><span>Documents with accepted versions' in client.get('/').get_data(as_text=True)
    assert client.get(f'/documents/{document}/versions/{version}/download').data.startswith(b'%PDF-')
    replacement=upload_document(client,title='Historical policy',document_id=document,review_date='2028-01-01')
    assert replacement==document
    second=version_for(application,document,2)
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(Document,document).current_version_id==version
    assert accept_document(application,client,document,second).status_code==302
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(Document,document).current_version_id==second
        assert len(s.get(Document,document).versions)==2
    assert client.get(f'/documents/{document}/versions/{version}/download').status_code==200
    assert client.get(f'/documents/{document}/versions/{second}/download').status_code==200


def test_assigned_participant_and_evidence_access_revoked_on_reassignment(application,client):
    staff_id,person_id=setup_people(application,client)
    # An administrator links an existing local member; this does not create/grant a role.
    assert normal_post(client,f'/staff/{staff_id}/edit',staff_payload(application,staff_id,user_id=application.test_users['staff'])).status_code==302
    staff=login(application,'staff',ORG_A)
    assert b'Casey' in staff.get('/participants/assigned').data
    assert b'Sensitive assigned care description' in staff.get(f'/participants/{person_id}').data
    assert b'Casey' in staff.get('/my-compliance/').data
    document=upload_document(client,title='Participant consent original',link=f'participant:{person_id}')
    version=version_for(application,document)
    assert b'Participant consent original' not in staff.get(f'/participants/{person_id}').data
    assert staff.get(f'/participants/{person_id}/evidence/{version}').status_code==404
    assert accept_document(application,client,document).status_code==302
    assert b'Participant consent original' in staff.get(f'/participants/{person_id}').data
    assert staff.get(f'/participants/{person_id}/evidence/{version}').status_code==200
    # Global documents, worker profiles and unassigned participants remain unavailable.
    for path in ['/documents/',f'/documents/{document}',f'/staff/{staff_id}']:
        assert staff.get(path).status_code==403
    assert staff.get('/participants/nonexistent').status_code==404
    assert normal_post(staff,f'/participants/{person_id}/edit',participant_payload(application,person_id)).status_code==403
    assert normal_post(client,f'/participants/{person_id}/edit',participant_payload(application,person_id,key_worker_staff_id='')).status_code==302
    assert b'Casey' not in staff.get('/participants/assigned').data
    assert staff.get(f'/participants/{person_id}').status_code==404
    assert staff.get(f'/participants/{person_id}/evidence/{version}').status_code==404


def test_cross_tenant_profiles_files_and_forged_relationships(application,client):
    staff_id,person_id=setup_people(application,client)
    document=upload_document(client,link=f'participant:{person_id}')
    version=version_for(application,document);accept_document(application,client,document)
    other=login(application,'admin_b',ORG_B)
    for path in [f'/staff/{staff_id}',f'/staff/{staff_id}/edit',f'/participants/{person_id}',
                 f'/documents/{document}',f'/documents/{document}/versions/{version}/download',
                 f'/participants/{person_id}/evidence/{version}']:
        assert other.get(path).status_code==404,path
    assert normal_post(other,f'/staff/{staff_id}/edit',staff_payload(application,staff_id)).status_code==404
    assert normal_post(client,f'/staff/{staff_id}/edit',staff_payload(application,staff_id,user_id=application.test_users['admin_b'])).status_code==400
    assert client.post(f'/staff/{staff_id}/edit',data=staff_payload(application,staff_id)).status_code==400


def test_credential_verification_and_new_original_requires_reverification(application,client):
    staff_id,_=setup_people(application,client)
    job=stage(client,table(['source_reference','staff_reference','credential_type','expiry_date'],
                         [['C-01','S-01','First Aid','2026-01-01']]),'credential')
    approve(client,job,state(application,job));credential=state(application,job)[0]['destination_id']
    document=upload_document(client,document_kind='credential',link=f'credential:{credential}',issue_date='2025-01-01',expiry_date='2027-01-01')
    accept_document(application,client,document)
    version=version_for(application,document)
    manager=login(application,'manager',ORG_A)
    def verify_payload():
        with application.app_context(),tenant_session(ORG_A) as s:
            value=s.get(StaffCredential,credential)
            return dict(revision=fingerprint(value),version_id=s.get(Document,document).current_version_id,
                        reason='Original and identity checked',signoff='yes')
    url=f'/staff/{staff_id}/credentials/{credential}/verify'
    assert normal_post(client,url,verify_payload()).status_code==403
    assert normal_post(manager,url,verify_payload()).status_code==302
    with application.app_context(),tenant_session(ORG_A) as s:
        value=s.get(StaffCredential,credential)
        assert value.status=='verified' and value.expiry_date==date(2027,1,1)
    # The document's existing credential link must be retained in renewals.
    payload={'title':'Renewal','document_id':document,'document_kind':'credential','expiry_date':'2028-01-01',
             'file':(io.BytesIO(b'%PDF-1.4\nReplacement\n'),'renewal.pdf')}
    assert normal_post(client,'/documents/upload',payload,content_type='multipart/form-data').status_code==400
    upload_document(client,title='Renewal',document_id=document,document_kind='credential',link=f'credential:{credential}',expiry_date='2028-01-01')
    second=version_for(application,document,2)
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(StaffCredential,credential).status=='verified'  # pending version does not supersede
    assert accept_document(application,client,document,second).status_code==302
    with application.app_context(),tenant_session(ORG_A) as s:
        value=s.get(StaffCredential,credential)
        assert value.status=='pending' and value.verified_at is None
        assert value.expiry_date==date(2027,1,1)  # dates change on separate credential verification
    assert normal_post(manager,url,verify_payload()).status_code==302
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(StaffCredential,credential).expiry_date==date(2028,1,1)


def test_per_version_participant_link_prevents_document_history_leaks(application,client):
    staff_id,person_id=setup_people(application,client)
    normal_post(client,f'/staff/{staff_id}/edit',staff_payload(application,staff_id,user_id=application.test_users['staff']))
    with application.app_context(),tenant_session(ORG_A) as s:
        other=Participant(first_name='Unassigned',last_name='Person');s.add(other);s.flush();other_id=other.id
    document=upload_document(client,link=f'participant:{other_id}',title='Restricted historical original')
    old=version_for(application,document);accept_document(application,client,document)
    upload_document(client,document_id=document,link=f'participant:{person_id}',title='Shared logical history')
    new=version_for(application,document,2);accept_document(application,client,document,new)
    staff=login(application,'staff',ORG_A)
    assert staff.get(f'/participants/{person_id}/evidence/{new}').status_code==200
    assert staff.get(f'/participants/{person_id}/evidence/{old}').status_code==404
    assert staff.get(f'/participants/{other_id}/evidence/{old}').status_code==404


def test_filters_escape_search_and_normal_pages_do_not_render_executable_input(application,client):
    staff_id,person_id=setup_people(application,client)
    assert normal_post(client,f'/staff/{staff_id}/edit',staff_payload(application,staff_id,job_title='<script>alert(1)</script>')).status_code==302
    assert b'<script>alert(1)</script>' not in client.get('/staff/').data
    assert b'&lt;script&gt;alert(1)&lt;/script&gt;' in client.get('/staff/').data
    assert b'worker@example.test' not in client.get('/staff/?q=does-not-match').data
    assert b'worker@example.test' not in client.get('/staff/?active=no').data
    assert b'Casey' not in client.get('/participants/?q=does-not-match').data
    assert client.get('/documents/?tab=unknown').status_code==400
    for path in ['/staff/','/participants/','/documents/','/']:
        assert client.get(path).headers['Cache-Control']=='private, no-store'
