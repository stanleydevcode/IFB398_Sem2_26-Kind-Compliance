"""Bounded readers: explicit headers, no formulas, no silent column loss."""
import csv
import io
from datetime import date, datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from openpyxl import load_workbook

MAX_ROWS = 2000
MAX_COLUMNS = 80
MAX_CELL = 10000


class MigrationError(ValueError):
    pass


def check_office_zip(data, required):
    try:
        with ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(x.file_size for x in entries) > 40 * 1024 * 1024:
                raise MigrationError("Office file expands beyond the 40 MiB safety limit.")
            names = {x.filename for x in entries}
            if required not in names or any("vbaproject" in n.lower() for n in names):
                raise MigrationError("Unsupported or macro-enabled Office file.")
    except BadZipFile as exc:
        raise MigrationError("Invalid Office file.") from exc


def read_table(data, filename):
    suffix = Path(filename).suffix.lower()
    workbook = None
    if suffix == ".csv":
        try:
            source = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise MigrationError("Save the CSV as UTF-8 and try again.") from exc
        csv.field_size_limit(MAX_CELL)
        rows = csv.reader(io.StringIO(source, newline=""), strict=True)
    elif suffix == ".xlsx":
        check_office_zip(data, "xl/workbook.xml")
        try:
            workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=False, keep_links=False)
            if len(workbook.worksheets) != 1:
                raise MigrationError("Upload one worksheet per file; export other sheets separately.")
            sheet = workbook.worksheets[0]
            if (sheet.max_column or 0) > MAX_COLUMNS or (sheet.max_row or 0) > MAX_ROWS + 1:
                raise MigrationError("Workbook exceeds 2,000 rows or 80 columns. Remove unused formatted cells.")
            rows = sheet.iter_rows(values_only=True)
        except MigrationError:
            if workbook:
                workbook.close()
            raise
        except Exception as exc:
            if workbook:
                workbook.close()
            raise MigrationError("Unable to read this XLSX workbook.") from exc
    else:
        raise MigrationError("Structured imports accept .csv or .xlsx only.")
    try:
        headers = [str(x).strip() if x is not None else "" for x in next(rows, [])]
        if not headers or len(headers) > MAX_COLUMNS or any(not x or len(x) > 150 for x in headers):
            raise MigrationError("Use 1–80 non-empty column headings, each at most 150 characters.")
        if len({x.casefold() for x in headers}) != len(headers):
            raise MigrationError("Duplicate column headings are not allowed.")
        result = []
        for number, values in enumerate(rows, 2):
            if number > MAX_ROWS + 1:
                raise MigrationError("Maximum 2,000 source rows per import.")
            if not any(x is not None and str(x).strip() for x in values):
                continue
            if len(values) != len(headers):
                raise MigrationError(f"Row {number} has a different column count from the headings.")
            record = {}
            for header, value in zip(headers, values):
                # Excel formula strings are retained as errors, never evaluated.
                if isinstance(value, (date, datetime)):
                    value = value.isoformat()
                value = "" if value is None else str(value).strip()
                if len(value) > MAX_CELL or "\x00" in value:
                    raise MigrationError(f"Row {number} contains an oversized or invalid cell.")
                record[header] = value
            result.append((number, record))
        if not result:
            raise MigrationError("The file contains headings but no records.")
        return headers, result
    except (csv.Error, ValueError) as exc:
        if isinstance(exc, MigrationError):
            raise
        raise MigrationError("Malformed table; check quoting and cell lengths.") from exc
    finally:
        if workbook:
            workbook.close()
