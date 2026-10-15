from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import select, func

from app.models import (Document, DocumentVersion, OrganisationRequirement, EvidenceLink,
                        StaffCredential, Staff, Participant)
from app.models.migration import MigrationAttachment
from app.services import record_pages as pages
from app.services.migration.documents import upload_document, review_document
from app.services.migration.engine import MODELS, label
from app.services.migration.reader import MigrationError
from app.services.migration import storage

bp = Blueprint("documents", __name__, url_prefix="/documents")
pages.install_guards(bp)


@bp.get("/")
@pages.page
def index():
    pages.manager()
    tenant = g.records_db
    tab = request.args.get("tab","library")
    if tab not in {"library","pending","requirements"}:
        abort(400)
    search = request.args.get("q","").strip()[:100]
    current = select(Document).join(DocumentVersion,Document.current_version_id == DocumentVersion.id).where(
        DocumentVersion.approval_status == "approved")
    if search:
        current = current.where(Document.title.icontains(search,autoescape=True))
    documents, number, more = pages.paginate(tenant,current.order_by(Document.title,Document.id))
    pending = tenant.scalars(select(DocumentVersion).where(DocumentVersion.approval_status == "pending")
                             .order_by(DocumentVersion.uploaded_at.desc()).limit(200)).all() if tab == "pending" else []
    requirements = tenant.scalars(select(OrganisationRequirement)).all() if tab == "requirements" else []
    counts = dict(accepted=tenant.scalar(select(func.count()).select_from(Document).join(DocumentVersion,
        Document.current_version_id == DocumentVersion.id).where(DocumentVersion.approval_status == "approved")),
        pending=tenant.scalar(select(func.count()).select_from(DocumentVersion).where(DocumentVersion.approval_status == "pending")))
    return render_template("documents/index.html",documents=documents,pending=pending,requirements=requirements,
                           counts=counts,tab=tab,page=number,more=more,search=search)


@bp.route("/upload",methods=["GET","POST"])
@pages.page
def upload():
    pages.manager()
    tenant = g.records_db
    if request.method == "POST":
        filename,contents = storage.receive(request.files.get("file"))
        form = request.form.to_dict()
        link = form.pop("link","")
        if link:
            form["linked_type"],separator,form["linked_id"] = link.partition(":")
            if not separator:
                raise MigrationError("Choose a valid related record.")
        key = None
        try:
            version,key = upload_document(tenant,g.records_org,current_user.id,filename,contents,form,audit_prefix="documents")
            tenant.commit()
        except Exception:
            if key:
                storage.resolve(g.records_org,key).unlink(missing_ok=True)
            raise
        flash("Original retained. Review the pending version before it becomes current.","success")
        return redirect(url_for("documents.detail",document_id=version.document_id))
    existing = pages.record(Document,request.args["document_id"]) if request.args.get("document_id") else None
    targets = []
    for kind,model in MODELS.items():
        query = select(model).limit(500)
        if kind in {"incident","complaint"}:
            query = query.where(model.case_type == kind)
        for item in tenant.scalars(query):
            title = label(item)
            if kind == "credential":
                title = f"{item.staff.first_name} {item.staff.last_name} · {item.credential_type.name}"
            targets.append(dict(kind=kind,id=item.id,label=title))
    requirements = tenant.scalars(select(OrganisationRequirement)).all()
    selected_link = request.args.get("link", "")
    if not selected_link and existing:
        meta = tenant.scalar(select(MigrationAttachment).join(DocumentVersion,
            MigrationAttachment.document_version_id == DocumentVersion.id).where(
            DocumentVersion.document_id == existing.id).order_by(DocumentVersion.version_no.desc()).limit(1))
        if meta and meta.linked_type:
            selected_link = f"{meta.linked_type}:{meta.linked_id}"
    return render_template("documents/upload.html",document=existing,targets=targets,requirements=requirements,
        selected_link=selected_link)


@bp.get("/<document_id>")
@pages.page
def detail(document_id):
    pages.manager()
    tenant = g.records_db
    document = pages.record(Document,document_id)
    versions = []
    for version in sorted(document.versions,key=lambda x:-x.version_no):
        meta = tenant.scalar(select(MigrationAttachment).filter_by(document_version_id=version.id))
        target = None
        if meta and meta.linked_type in MODELS and meta.linked_id:
            linked = tenant.get(MODELS[meta.linked_type],meta.linked_id)
            if linked:
                target = dict(kind=meta.linked_type,id=linked.id,label=label(linked))
                if meta.linked_type == "credential":
                    target["staff_id"] = linked.staff_id
        versions.append(dict(version=version,metadata=meta,target=target))
    current_meta = next((x["metadata"] for x in versions if x["version"].id == document.current_version_id), None)
    current_meta = current_meta or (versions[0]["metadata"] if versions else None)
    replacement_link = f"{current_meta.linked_type}:{current_meta.linked_id}" if current_meta and current_meta.linked_type else ""
    return render_template("documents/detail.html",document=document,versions=versions,replacement_link=replacement_link)


@bp.post("/<document_id>/versions/<version_id>/review")
@pages.page
def review(document_id,version_id):
    pages.manager()
    document = pages.record(Document,document_id)
    version = pages.record(DocumentVersion,version_id)
    if version.document_id != document.id:
        abort(404)
    if request.form.get("signoff") != "yes":
        raise MigrationError("Confirm you checked the original and entered metadata before review.")
    review_document(g.records_db,g.records_org,version.id,current_user.id,request.form.get("decision"),
                    request.form.get("notes",""),audit_prefix="documents")
    flash("Document review saved. Credential verification remains separate.","success")
    return redirect(url_for("documents.detail",document_id=document.id))


@bp.get("/<document_id>/versions/<version_id>/download")
@pages.page
def download(document_id,version_id):
    pages.manager()
    document = pages.record(Document,document_id)
    version = pages.record(DocumentVersion,version_id)
    if version.document_id != document.id:
        abort(404)
    return pages.download_version(g.records_db,version.id)
