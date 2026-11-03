"""Bounded format adapters. No spreadsheet formula engine is invoked."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

from . import core

FORMATS = ("csv", "tsv", "json", "jsonl", "xlsx")


def detect_format(path: Path, file_format: str, data: bytes | None = None) -> str:
    if file_format != "auto":
        if file_format not in FORMATS:
            raise core.ProbeFileError("Unknown format; choose csv, tsv, json, jsonl or xlsx")
        return file_format
    suffix = path.suffix.lower().lstrip(".")
    if suffix in FORMATS:
        return suffix
    if data is not None:
        if data.startswith(b"PK\x03\x04"):
            return "xlsx"
        sample = data[:8192].lstrip(b"\xef\xbb\xbf \t\r\n")
        if sample.startswith(b"["):
            return "json"
        if sample.startswith(b"{"):
            return "jsonl"
        if b"_rowcanary_id" in sample.split(b"\n", 1)[0]:
            return "tsv" if b"\t" in sample.split(b"\n", 1)[0] else "csv"
        raise core.ProbeFileError("Unknown format; use --format to select the parser")
    return "csv"


def _load_xlsx(data: bytes):
    from openpyxl import load_workbook

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len({entry.filename for entry in entries}) != len(entries):
                raise core.ProbeFileError("XLSX has duplicate archive members")
            if len(entries) > 1000 or sum(e.file_size for e in entries) > 64 * 1024 * 1024:
                raise core.ProbeFileError("XLSX expanded archive exceeds the safety limit")
            if any(e.flag_bits & 1 for e in entries):
                raise core.ProbeFileError("Encrypted XLSX files are unsupported")
        workbook = load_workbook(
            io.BytesIO(data), read_only=True, data_only=False, keep_links=False
        )
        try:
            if len(workbook.worksheets) != 1:
                raise core.ProbeFileError("XLSX must contain exactly one worksheet")
            sheet = workbook.worksheets[0]
            if sheet.max_row and sheet.max_row > core.MAX_ROWS + 1:
                raise core.ProbeFileError("XLSX has too many rows")
            if sheet.max_column and sheet.max_column > 1024:
                raise core.ProbeFileError("XLSX has too many columns")
            rows = []
            columns = None
            for cells in sheet.iter_rows():
                values = [
                    "" if c.value is None and c.data_type == "inlineStr" else c.value for c in cells
                ]
                if any(isinstance(v, str) and len(v) > core.MAX_FIELD_CHARS for v in values):
                    raise core.ProbeFileError("XLSX field exceeds the safety limit")
                if any(c.data_type == "f" for c in cells):
                    raise core.ProbeFileError(
                        "XLSX contains formulas; export formulas as literal text first"
                    )
                if columns is None:
                    columns = values
                    if (
                        not columns
                        or any(not isinstance(c, str) or not c for c in columns)
                        or len(set(columns)) != len(columns)
                    ):
                        raise core.ProbeFileError("XLSX requires unique text column headers")
                else:
                    if len(rows) >= core.MAX_ROWS:
                        raise core.ProbeFileError("XLSX has too many rows")
                    rows.append(dict(zip(columns, values)))
            return rows, columns or []
        finally:
            workbook.close()
    except core.ProbeFileError:
        raise
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ParseError) as exc:
        raise core.ProbeFileError("Malformed or unsupported XLSX: " + str(exc)) from exc


def load_rows(path: Path, file_format: str, delimiter: str, encoding: str):
    data = core._read_bytes(path)
    fmt = detect_format(path, file_format, data)
    if fmt == "xlsx":
        rows, columns = _load_xlsx(data)
    else:
        text = core._decode_text(data, encoding)
        if fmt in ("csv", "tsv"):
            sep = "\t" if fmt == "tsv" else delimiter
            core._validate_delimiter(sep)
            rows, columns = core._load_csv(text, delimiter=sep)
        elif fmt == "json":
            rows = core._load_json(text)
            columns = None
        else:
            rows = []
            for number, line in enumerate(io.StringIO(text, newline=""), 1):
                if not line.strip():
                    raise core.ProbeFileError(f"JSONL line {number} is blank")
                if len(rows) >= core.MAX_ROWS:
                    raise core.ProbeFileError("JSONL has too many rows")
                row = core._load_json("[" + line + "]")
                if len(row) != 1:
                    raise core.ProbeFileError("JSONL requires exactly one object per line")
                rows.extend(row)
            columns = None
    return rows, columns, fmt


def encode_probes(probes, fmt: str, delimiter: str, encoding: str) -> bytes:
    records = [{core.ID_COLUMN: p.ident, core.VALUE_COLUMN: p.value} for p in probes]
    if fmt == "xlsx":
        from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

        for p in probes:
            if isinstance(p.value, str) and (
                len(p.value) > 32767 or ILLEGAL_CHARACTERS_RE.search(p.value)
            ):
                raise core.ProbeFileError(
                    "XLSX text must fit 32767 characters and contain no XML control characters"
                )
            if type(p.value) is int and abs(p.value) > 999999999999999:
                raise core.ProbeFileError(
                    "XLSX integer may lose precision; use text for large integers"
                )
            if len(p.ident) > 32767 or ILLEGAL_CHARACTERS_RE.search(p.ident):
                raise core.ProbeFileError("XLSX ID is not valid bounded cell text")
        # A small OpenXML writer avoids platform text-newline translation in
        # third-party worksheet writers. Every string is an inline literal.
        namespace = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        sheet = ElementTree.Element("worksheet", xmlns=namespace)
        rows = ElementTree.SubElement(sheet, "sheetData")
        for index, values in enumerate(
            [(core.ID_COLUMN, core.VALUE_COLUMN)] + [(p.ident, p.value) for p in probes], 1
        ):
            row = ElementTree.SubElement(rows, "row", r=str(index))
            for column, value in zip(("A", "B"), values):
                cell = ElementTree.SubElement(row, "c", r=f"{column}{index}")
                if isinstance(value, str):
                    cell.set("t", "inlineStr")
                    inline = ElementTree.SubElement(cell, "is")
                    text = ElementTree.SubElement(inline, "t", {"xml:space": "preserve"})
                    text.text = value
                elif value is not None:
                    cell.set("t", "b" if type(value) is bool else "n")
                    ElementTree.SubElement(cell, "v").text = (
                        str(int(value)) if type(value) is bool else repr(value)
                    )
        parts = {
            "[Content_Types].xml": b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
            "_rels/.rels": b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
            "xl/workbook.xml": b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="RowCanary" sheetId="1" r:id="rId1"/></sheets></workbook>',
            "xl/_rels/workbook.xml.rels": b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
            "xl/worksheets/sheet1.xml": ElementTree.tostring(
                sheet, encoding="utf-8", xml_declaration=True
            ).replace(b"\r", b"&#13;"),
        }
        output = io.BytesIO()
        # Stored members avoid host zlib-version differences in synthetic bytes.
        with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as target:
            for name, content in sorted(parts.items()):
                info = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o600 << 16
                info.compress_type = zipfile.ZIP_STORED
                target.writestr(info, content)
        return output.getvalue()
    if fmt in ("csv", "tsv"):
        sep = "\t" if fmt == "tsv" else delimiter
        core._validate_delimiter(sep)
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=sep, lineterminator="\r\n")
        writer.writerow([core.ID_COLUMN, core.VALUE_COLUMN])
        writer.writerows((p.ident, p.value) for p in probes)
        text = output.getvalue()
    elif fmt == "json":
        text = json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    else:
        text = "".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in records)
    try:
        return text.encode(encoding)
    except (UnicodeError, LookupError) as exc:
        raise core.ProbeFileError(
            "Cannot encode probes; choose an encoding that supports every value"
        ) from exc
