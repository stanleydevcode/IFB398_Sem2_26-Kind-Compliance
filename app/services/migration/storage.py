"""Opaque private keys; original filenames never become filesystem paths."""
import hashlib
import io
from pathlib import Path
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename

from app.services.migration.reader import MigrationError, check_office_zip
from app.services.tenant import schema_name_for_organisation

MAX_FILE = 10 * 1024 * 1024
ALLOWED = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".csv", ".xlsx"}


def receive(upload):
    if not upload or not upload.filename:
        raise MigrationError("Choose a file.")
    filename = secure_filename(upload.filename)[:240]
    if not filename:
        raise MigrationError("Invalid filename.")
    data = upload.read(MAX_FILE + 1)
    if not data or len(data) > MAX_FILE:
        raise MigrationError("Choose a non-empty file up to 10 MiB.")
    return filename, data


def validate_document(filename, data):
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise MigrationError("Supported: PDF, DOC/DOCX, JPG/PNG/TIFF, CSV and XLSX.")
    signatures = {".pdf": (b"%PDF-",), ".png": (b"\x89PNG\r\n\x1a\n",),
                  ".jpg": (b"\xff\xd8\xff",), ".jpeg": (b"\xff\xd8\xff",),
                  ".tif": (b"II*\x00", b"MM\x00*"), ".tiff": (b"II*\x00", b"MM\x00*"),
                  ".doc": (bytes.fromhex("d0cf11e0a1b11ae1"),)}
    if suffix in signatures and not data.startswith(signatures[suffix]):
        raise MigrationError("The file content does not match its extension.")
    if suffix in {".docx", ".xlsx"}:
        check_office_zip(data, "word/document.xml" if suffix == ".docx" else "xl/workbook.xml")
    if suffix == ".csv":
        try:
            if "\x00" in data.decode("utf-8-sig"):
                raise ValueError()
        except (UnicodeDecodeError, ValueError) as exc:
            raise MigrationError("CSV attachments must be UTF-8 text.") from exc


def root():
    return Path(current_app.config.get("MIGRATION_STORAGE_ROOT") or
                Path(current_app.instance_path) / "migration_private").resolve()


def resolve(organisation_id, key):
    base = (root() / schema_name_for_organisation(organisation_id)).resolve()
    target = (root() / key).resolve()
    if not target.is_relative_to(base):
        raise MigrationError("Invalid private file reference.")
    return target


def save(organisation_id, data):
    key = f"{schema_name_for_organisation(organisation_id)}/{uuid4().hex}"
    target = resolve(organisation_id, key)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with target.open("xb") as file:
        file.write(data)
    target.chmod(0o600)
    return key, hashlib.sha256(data).hexdigest()


def verified_bytes(organisation_id, key, expected_hash):
    try:
        data = resolve(organisation_id, key).read_bytes()
    except OSError as exc:
        raise MigrationError("Original file is unavailable; restore it from backup.") from exc
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise MigrationError("File integrity check failed. Contact the administrator.")
    return io.BytesIO(data)
