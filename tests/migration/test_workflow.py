import csv
import io
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import pytest
from openpyxl import Workbook
from sqlalchemy import select, func

from app.models import Staff, Participant, StaffCredential, Case, Risk, Document, DocumentVersion, AuditLog
from app.models.migration import MigrationJob, MigrationRow, SourceIdentity, MigrationChange
from app.services.tenant import tenant_session
from app.services.migration.engine import fingerprint
from app.services.migration.reader import read_table, MigrationError
from app.services.migration.storage import MAX_FILE
from conftest import ORG_A, ORG_B, login, post


def table(headers, rows):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(headers)
    w.writerows(rows)
    return out.getvalue().encode()


def stage(client, data, kind="staff", system="Legacy demo", mapping=None, date_format="iso"):
    response = post(client, "/migration/upload", {"record_type": kind, "source_system": system,
                    "file": (io.BytesIO(data), "history.csv")}, content_type="multipart/form-data")
    assert response.status_code == 302, response.get_data(as_text=True)
    job_id = response.location.split("/")[-2]
    mapping_data = {"date_format": date_format}
    headers = read_table(data,"history.csv")[0]
    mapping_data.update({"map_"+key: value for key,value in (mapping or {h:h for h in headers}).items()})
    response = post(client, response.location, mapping_data)
    assert response.status_code == 302, response.get_data(as_text=True)
    return job_id


def state(app, job_id, org=ORG_A):
    with app.app_context(), tenant_session(org) as s:
        job = s.get(MigrationJob, job_id)
        return [{"id":r.id,"state":r.status,"data":r.data,"destination_id":r.destination_id,
                 "candidates":r.candidates,"errors":r.errors,"decision":r.decision} for r in job.rows]


def approve(client, job_id, rows):
    return post(client,f"/migration/{job_id}/approve",{"rows": [r["id"] for r in rows], "signoff":"yes"})


def review(client, job_id, row, data=None, decision="create", target_id="", reason=""):
    url=f"/migration/{job_id}/rows/{row['id']}"
    html=client.get(url).get_data(as_text=True)
    rev=re.search(r'name="revision" value="([^"]+)"',html).group(1)
    payload={"revision":rev,"decision":decision,"target_id":target_id,"reason":reason}
    context=re.search(r'name="review_token" value="([^"]+)"',html)
    if context:
        payload["review_token"]=context.group(1)
    payload.update({"field_"+k:v for k,v in (data if data is not None else row["data"]).items()})
    return post(client,url,payload)


def staff_file(reference="S-01", email="worker@example.test", first="Alex"):
    return table(["source_reference","first_name","last_name","email"], [[reference,first,"Sample",email]])


def test_partial_approval_corrections_live_models_and_reconciliation(application, client):
    data=table(["source_reference","first_name","last_name","email"],
               [["S-01","Alex","Sample","alex@example.test"],["S-02","","Sample","not-email"]])
    job=stage(client,data)
    rows=state(application,job)
    assert [r["state"] for r in rows]==["ready","invalid"]
    with application.app_context(), tenant_session(ORG_A) as s:
        assert s.scalar(select(func.count()).select_from(Staff))==0
    assert approve(client,job,rows).status_code==302
    rows=state(application,job)
    assert [r["state"] for r in rows]==["imported","invalid"]
    correction={**rows[1]["data"],"first_name":"Jamie","email":"jamie@example.test"}
    assert review(client,job,rows[1],correction).status_code==302
    assert approve(client,job,state(application,job)).status_code==302
    # A repeated submission is idempotent.
    assert approve(client,job,state(application,job)).status_code==302
    with application.app_context(), tenant_session(ORG_A) as s:
        assert s.scalar(select(func.count()).select_from(Staff))==2
        assert s.get(MigrationJob,job).status=="complete"
        assert all(x.user_id is None for x in s.scalars(select(Staff)))
        assert s.scalar(select(func.count()).select_from(SourceIdentity))==2
    csv_data=client.get(f"/migration/{job}/reconciliation.csv")
    assert csv_data.status_code==200 and b"imported" in csv_data.data
    assert client.get("/migration/records/staff").status_code==200
    assert client.get(f"/migration/{job}/preview").status_code==200
    assert client.get("/migration/").status_code==200


def test_duplicates_require_review_and_update_preserves_id_and_history(application,client):
    job=stage(client,staff_file())
    approve(client,job,state(application,job))
    old=state(application,job)[0]["destination_id"]
    second=stage(client,staff_file(first="Alex Corrected"))
    row=state(application,second)[0]
    assert row["state"]=="duplicate"
    approve(client,second,[row])
    assert state(application,second)[0]["state"]=="duplicate"
    assert review(client,second,row,decision="update",target_id=old,reason="Checked the historical export spelling").status_code==302
    approve(client,second,state(application,second))
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.scalar(select(func.count()).select_from(Staff))==1
        assert s.get(Staff,old).first_name=="Alex Corrected"
        history=s.scalar(select(MigrationChange))
        assert history.before["first_name"]=="Alex"
        assert history.after["first_name"]=="Alex Corrected"
        # General audit log references IDs rather than sensitive source narratives.
        assert "Alex Corrected" not in str([a.changes for a in s.scalars(select(AuditLog))])


def test_create_new_requires_different_source_identity_and_reason(application,client):
    job=stage(client,staff_file())
    approve(client,job,state(application,job))
    second=stage(client,staff_file())
    row=state(application,second)[0]
    review(client,second,row,decision="create_new",reason="Different person")
    assert state(application,second)[0]["state"]=="invalid"
    row=state(application,second)[0]
    review(client,second,row,{**row["data"],"source_reference":"S-02"},decision="create_new",reason="Same name; checked different staff identity")
    approve(client,second,state(application,second))
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.scalar(select(func.count()).select_from(Staff))==2


def test_duplicate_race_rechecked_between_staged_jobs(application,client):
    a=stage(client,staff_file())
    b=stage(client,staff_file())
    approve(client,a,state(application,a))
    approve(client,b,state(application,b))
    assert state(application,b)[0]["state"]=="duplicate"


def test_stale_update_is_not_overwritten(application,client):
    a=stage(client,staff_file());approve(client,a,state(application,a))
    b=stage(client,staff_file(first="Correction"));row=state(application,b)[0]
    target=state(application,a)[0]["destination_id"]
    review(client,b,row,decision="update",target_id=target,reason="Correction reviewed")
    with application.app_context(),tenant_session(ORG_A) as s:
        s.get(Staff,target).phone="0412345678"
    approve(client,b,state(application,b))
    assert state(application,b)[0]["state"]=="invalid"
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(Staff,target).first_name=="Alex"


def test_tenant_isolation_rbac_csrf_originals_and_forged_links(application,client):
    job=stage(client,staff_file())
    assert client.get(f"/migration/{job}/original").status_code==200
    other=login(application,"admin_b",ORG_B)
    for path in [f"/migration/{job}/preview",f"/migration/{job}/original",f"/migration/{job}/reconciliation.csv"]:
        assert other.get(path).status_code==404
    assert post(other,f"/migration/{job}/approve",{"rows":[state(application,job)[0]["id"]],"signoff":"yes"}).status_code==404
    assert application.test_client().get("/migration/").status_code==302
    staff=login(application,"staff",ORG_A)
    for path in ["/migration/","/migration/documents","/migration/templates/staff.csv","/migration/records/participant"]:
        assert staff.get(path).status_code==403
    manager=login(application,"manager",ORG_A)
    assert manager.get("/migration/").status_code==200
    assert client.post("/migration/upload",data={}).status_code==400
    assert client.post("/migration/upload",data={"csrf_token":"forged"}).status_code==400
    # Import staff in B only. A cannot use its legacy ref for a credential.
    b=stage(other,staff_file());approve(other,b,state(application,b,ORG_B))
    cred=stage(client,table(["source_reference","staff_reference","credential_type","expiry_date"],[["C-01","S-01","First Aid","2027-01-01"]]),"credential")
    assert state(application,cred)[0]["state"]=="invalid"


def test_related_types_historical_dates_and_credential_verification(application,client):
    staff=stage(client,staff_file());approve(client,staff,state(application,staff))
    participant=stage(client,table(["source_reference","first_name","last_name","key_worker_reference","date_of_birth"],
        [["P-01","Casey","Example","S-01","1990-03-04"]]),"participant")
    approve(client,participant,state(application,participant))
    cred=stage(client,table(["source_reference","staff_reference","credential_type","issue_date","expiry_date"],
        [["C-01","S-01","First Aid","2023-01-01","2024-01-01"]]),"credential")
    approve(client,cred,state(application,cred))
    headers=["source_reference","category","description","occurred_at","reported_at","severity","status","reportability","participant_reference","reporter_reference","closed_at","outcome"]
    for kind in ["incident","complaint"]:
        case=stage(client,table(headers,[["CASE-01","historical","Fictional historical case","2025-01-01T09:00:00+10:00","2025-01-01T10:00:00+10:00","low","closed","requires_review","P-01","S-01","2025-01-02T12:00:00+10:00","Reviewed in historical register"]]),kind)
        assert state(application,case)[0]["state"]=="ready"
        approve(client,case,state(application,case))
    risk=stage(client,table(["source_reference","title","likelihood","consequence","status","owner_reference"],
        [["R-01","Example risk","2","4","monitoring","S-01"]]),"risk")
    approve(client,risk,state(application,risk))
    with application.app_context(),tenant_session(ORG_A) as s:
        credential=s.scalar(select(StaffCredential))
        assert credential.status=="pending" and credential.verified_at is None
        assert credential.expiry_date==date(2024,1,1)
        person=s.scalar(select(Participant));assert person.key_worker_staff_id==s.scalar(select(Staff.id))
        cases=s.scalars(select(Case)).all();assert len(cases)==2
        assert all(c.occurred_at.year==2024 and c.reported_at.year==2025 and c.imported_at is not None for c in cases)
        assert all(c.reportable_to_ndis is None for c in cases)
        assert s.scalar(select(Risk)).rating is None  # no invented matrix
    assert client.get("/migration/records/incident").status_code==200
    assert client.get("/migration/records/credential").status_code==200


def test_mapping_dates_ignored_org_and_unknown_fields(application,client):
    raw=table(["Old ID","Given","Family","Started","organisation_id"],[["S-01","Alex","Sample","04/05/2025",ORG_B]])
    job=stage(client,raw,mapping={"source_reference":"Old ID","first_name":"Given","last_name":"Family","start_date":"Started"},date_format="dmy")
    row=state(application,job)[0]
    assert row["data"]["start_date"]=="2025-05-04"
    approve(client,job,[row])
    with application.app_context(),tenant_session(ORG_B) as s:
        assert s.scalar(select(func.count()).select_from(Staff))==0


def test_transaction_rolls_back_all_selected_writes_on_database_failure(application,client,monkeypatch):
    from app.services.migration import engine
    job=stage(client,table(["source_reference","first_name","last_name"],[["S-01","A","Sample"],["S-02","B","Sample"]]))
    original=engine.destination_values
    calls=[]
    def failing(s,row):
        calls.append(row.id)
        if len(calls)==2:
            raise MigrationError("Simulated failure")
        return original(s,row)
    monkeypatch.setattr(engine,"destination_values",failing)
    assert approve(client,job,state(application,job)).status_code==400
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.scalar(select(func.count()).select_from(Staff))==0
        assert all(r.status=="ready" for r in s.get(MigrationJob,job).rows)


def test_skip_cancel_and_signoff(application,client):
    job=stage(client,staff_file());row=state(application,job)[0]
    assert post(client,f"/migration/{job}/approve",{"rows":[row["id"]]}).status_code==400
    assert review(client,job,row,decision="skip",reason="Not in cutover scope").status_code==302
    assert state(application,job)[0]["state"]=="skipped"
    other=stage(client,staff_file(reference="S-02"))
    assert post(client,f"/migration/{other}/cancel").status_code==302
    assert approve(client,other,state(application,other)).status_code==400


def test_headers_bounds_formulas_and_excel():
    for contents in [b"a,a\n1,2\n",b"a,b\n1,2,3\n", b"\xff\xff", b"a,b\n",b",b\n1,2\n"]:
        with pytest.raises(MigrationError):
            read_table(contents,"bad.csv")
    with pytest.raises(MigrationError):
        read_table(table(["name"],[["x"]]*2001),"too-many.csv")
    workbook=Workbook();sheet=workbook.active;sheet.append(["first_name","last_name"]);sheet.append(["Alex","Sample"])
    out=io.BytesIO();workbook.save(out)
    assert read_table(out.getvalue(),"one.xlsx")[1][0][1]["first_name"]=="Alex"
    workbook.create_sheet("other");out=io.BytesIO();workbook.save(out)
    with pytest.raises(MigrationError):read_table(out.getvalue(),"two.xlsx")


def test_formula_rows_remain_in_review(application,client):
    job=stage(client,table(["first_name","last_name"],[["=HYPERLINK(\"http://example.test\")","Sample"]]))
    assert state(application,job)[0]["state"]=="invalid"


def test_repeat_reference_within_file_only_first_can_proceed(application,client):
    job=stage(client,table(["source_reference","first_name","last_name"],[["S-01","A","One"],["S-01","B","Two"]]))
    assert [r["state"] for r in state(application,job)]==["ready","invalid"]
    approve(client,job,state(application,job))
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.scalar(select(func.count()).select_from(Staff))==1


def upload_doc(client,content=b"%PDF-1.4\nFictional test original\n", **values):
    form={"title":"Historical test policy","document_kind":"policy","review_date":"2027-01-01", **values}
    form["file"]=(io.BytesIO(content),"policy.pdf")
    return post(client,"/migration/documents",form,content_type="multipart/form-data")


def test_document_versions_downloads_reviews_and_integrity(application,client):
    original=b"%PDF-1.4\nOriginal signed example\n"
    response=upload_doc(client,original)
    assert response.status_code==302,response.get_data(as_text=True)
    url=response.location;document_id=url.rsplit("/",1)[-1]
    with application.app_context(),tenant_session(ORG_A) as s:
        doc=s.get(Document,document_id);assert doc.current_version_id is None
        v1=doc.versions[0].id
    assert client.get(url).status_code==200
    assert client.get(f"/migration/documents/versions/{v1}/download").data==original
    review_url=f"/migration/documents/versions/{v1}/review"
    assert post(client,review_url,{"decision":"approved","notes":"Original checked","signoff":"yes"}).status_code==302
    response=upload_doc(client,b"%PDF-1.4\nReplacement\n",document_id=document_id,review_date="2028-01-01")
    assert response.status_code==302
    with application.app_context(),tenant_session(ORG_A) as s:
        doc=s.get(Document,document_id);assert doc.current_version_id==v1
        v2=next(v.id for v in doc.versions if v.version_no==2)
    other=login(application,"admin_b",ORG_B)
    assert other.get(url).status_code==404
    assert other.get(f"/migration/documents/versions/{v1}/download").status_code==404
    assert post(client,f"/migration/documents/versions/{v2}/review",{"decision":"approved","notes":"Replacement checked","signoff":"yes"}).status_code==302
    with application.app_context(),tenant_session(ORG_A) as s:
        doc=s.get(Document,document_id);assert doc.current_version_id==v2
        assert len(doc.versions)==2 and doc.review_date==date(2028,1,1)
        from app.services.migration import storage
        storage.resolve(ORG_A,s.get(DocumentVersion,v1).file_path).write_bytes(b"tampered")
    assert client.get(f"/migration/documents/versions/{v1}/download").status_code==400


def test_invalid_files_and_forged_document_relationships(application,client):
    assert upload_doc(client,b"not a PDF").status_code==400
    assert upload_doc(client,b"%PDF-"+b"x"*MAX_FILE).status_code==400
    assert upload_doc(client,link="participant:nonexistent").status_code==400
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.scalar(select(func.count()).select_from(Document))==0
    assert not list(Path(application.config["MIGRATION_STORAGE_ROOT"]).glob("**/*"))


def test_credential_attachment_does_not_verify(application,client):
    j=stage(client,staff_file());approve(client,j,state(application,j))
    j=stage(client,table(["staff_reference","credential_type","expiry_date"],[["S-01","First Aid","2027-01-01"]]),"credential")
    approve(client,j,state(application,j));credential=state(application,j)[0]["destination_id"]
    response=upload_doc(client,document_kind="credential",link=f"credential:{credential}")
    assert response.status_code==302
    doc_id=response.location.rsplit("/",1)[-1]
    with application.app_context(),tenant_session(ORG_A) as s:
        version=s.get(Document,doc_id).versions[0].id
    post(client,f"/migration/documents/versions/{version}/review",{"decision":"approved","notes":"File checked","signoff":"yes"})
    with application.app_context(),tenant_session(ORG_A) as s:
        cred=s.get(StaffCredential,credential)
        assert cred.document_id==doc_id and cred.status=="pending" and cred.verified_at is None


def test_cli_upgrade_idempotent_and_catalogue(application):
    runner=application.test_cli_runner()
    assert runner.invoke(args=["migration-init"]).exit_code==0
    assert runner.invoke(args=["migration-init"]).exit_code==0
    assert runner.invoke(args=["migration-add-credential-type","CPR"]).exit_code==0
    assert runner.invoke(args=["migration-add-credential-type","CPR"]).exit_code==0


def test_supplied_historical_fixtures_end_to_end(application,client):
    from app.extensions import db
    from app.models import CredentialType
    from app.services.migration.storage import validate_document
    root=Path(__file__).resolve().parents[2]/"examples"/"migration"
    with application.app_context():
        db.session.add_all([CredentialType(name="CPR"),CredentialType(name="Worker Screening")]);db.session.commit()
    kinds=["staff","participant","credential","incident","complaint","risk"]
    for filename,kind,expected in zip(sorted((root/"history").glob("0[1-6]_*.csv")),kinds,[3,2,3,2,1,2]):
        job=stage(client,filename.read_bytes(),kind)
        rows=state(application,job)
        assert len(rows)==expected and all(r["state"]=="ready" for r in rows), (filename,rows)
        assert approve(client,job,rows).status_code==302
        assert all(r["state"]=="imported" for r in state(application,job))
    dirty=stage(client,(root/"review_cases/07_staff_needs_review.csv").read_bytes())
    assert [r["state"] for r in state(application,dirty)]==["duplicate","ready","invalid","invalid","invalid"]
    file=root/"history/09_provider_columns_staff.xlsx"
    response=post(client,"/migration/upload",{"record_type":"staff","source_system":"Legacy demo",
        "file":(io.BytesIO(file.read_bytes()),file.name)},content_type="multipart/form-data")
    assert response.status_code==302
    import json
    mapping=json.loads((root/"history/09_column_mapping.json").read_text())
    payload={"map_"+k:v for k,v in mapping.items()};payload["date_format"]="iso"
    assert post(client,response.location,payload).status_code==302
    xlsx_job=response.location.split("/")[-2]
    assert all(r["state"]=="ready" for r in state(application,xlsx_job))
    for original in (root/"documents").iterdir():
        validate_document(original.name,original.read_bytes())


def test_returned_version_retains_previous_and_older_pending_cannot_replace(application,client):
    response=upload_doc(client);document_id=response.location.rsplit("/",1)[-1]
    upload_doc(client,document_id=document_id)
    assert b"Identical file bytes already exist" in client.get(response.location).data
    with application.app_context(),tenant_session(ORG_A) as s:
        versions=sorted(s.get(Document,document_id).versions,key=lambda x:x.version_no)
        first,second=[v.id for v in versions]
    assert post(client,f"/migration/documents/versions/{second}/review",{"decision":"approved","notes":"Newer approved","signoff":"yes"}).status_code==302
    assert post(client,f"/migration/documents/versions/{first}/review",{"decision":"approved","notes":"Older pending","signoff":"yes"}).status_code==400
    assert post(client,f"/migration/documents/versions/{first}/review",{"decision":"returned","notes":"Superseded pending version","signoff":"yes"}).status_code==302
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(Document,document_id).current_version_id==second
        assert s.get(DocumentVersion,first).approval_status=="returned"


def test_sparse_updates_preserve_inactive_flag_and_stale_review_form(application,client):
    data=table(["source_reference","first_name","last_name","is_active"],[["S-01","Alex","Sample","no"]])
    j=stage(client,data);approve(client,j,state(application,j));target=state(application,j)[0]["destination_id"]
    j=stage(client,staff_file());row=state(application,j)[0]
    url=f"/migration/{j}/rows/{row['id']}"
    old_html=client.get(url).get_data(as_text=True)
    old_revision=re.search(r'name="revision" value="([^"]+)"',old_html).group(1)
    assert review(client,j,row,decision="update",target_id=target,reason="Add contact details").status_code==302
    assert post(client,url,{"revision":old_revision,"decision":"skip","reason":"Stale form"}).status_code==400
    approve(client,j,state(application,j))
    with application.app_context(),tenant_session(ORG_A) as s:
        assert s.get(Staff,target).is_active is False


def test_office_archive_validation_and_export_injection(application,client):
    from zipfile import ZipFile
    from app.services.migration.storage import validate_document
    with pytest.raises(MigrationError):validate_document('fake.docx',b'not a zip')
    out=io.BytesIO()
    with ZipFile(out,'w') as z:
        z.writestr('word/document.xml','<document/>')
        z.writestr('word/vbaProject.bin','blocked macro')
    with pytest.raises(MigrationError):validate_document('macro.docx',out.getvalue())
    job=stage(client,staff_file(reference='=1+1'))
    response=client.get(f"/migration/{job}/reconciliation.csv")
    assert b"'=1+1" in response.data
