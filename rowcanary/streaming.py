"""Context-managed, bounded streaming for line-oriented input formats."""

from __future__ import annotations

import csv
import io
from contextlib import contextmanager
from pathlib import Path

from . import core
from .formats import detect_format, load_rows


class _BoundedReader(io.RawIOBase):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream
        self.count = 0

    def readable(self):
        return True

    def readinto(self, buffer):
        size = min(len(buffer), core.MAX_BYTES - self.count + 1)
        count = self.stream.readinto(memoryview(buffer)[:size]) or 0
        self.count += count
        if self.count > core.MAX_BYTES:
            raise core.ProbeFileError("File exceeds the byte safety limit")
        return count


def _csv_records(reader, columns):
    for index, fields in enumerate(reader):
        if index >= core.MAX_ROWS:
            raise core.ProbeFileError("CSV has too many rows")
        if any(len(field) > core.MAX_FIELD_CHARS for field in fields):
            raise core.ProbeFileError("CSV field exceeds the safety limit")
        if len(fields) > len(columns):
            raise core.ProbeFileError(f"CSV row {reader.line_num} has extra fields")
        yield (
            {name: fields[i] if i < len(fields) else None for i, name in enumerate(columns)}
            if fields
            else {}
        )


def _jsonl_records(stream):
    for index, line in enumerate(stream):
        if not line.strip():
            raise core.ProbeFileError(f"JSONL line {index + 1} is blank")
        if index >= core.MAX_ROWS:
            raise core.ProbeFileError("JSONL has too many rows")
        rows = core._load_json("[" + line + "]")
        if len(rows) != 1:
            raise core.ProbeFileError("JSONL requires exactly one object per line")
        yield rows[0]


@contextmanager
def open_rows(path: Path, file_format: str, delimiter: str, encoding: str):
    """Yield (single-pass rows, headers or None, format); close on every exit."""
    path = Path(path)
    try:
        if not path.is_file():
            raise core.ProbeFileError(f"File does not exist: {path}")
        if path.stat().st_size > core.MAX_BYTES:
            raise core.ProbeFileError("File exceeds the byte safety limit")
        with path.open("rb", buffering=0) as raw:
            prefix = raw.read(min(8192, core.MAX_BYTES + 1))
            if len(prefix) > core.MAX_BYTES:
                raise core.ProbeFileError("File exceeds the byte safety limit")
            fmt = detect_format(path, file_format, prefix)
            if fmt not in ("csv", "tsv", "jsonl"):
                yield load_rows(path, fmt, delimiter, encoding)
                return
            raw.seek(0)
            if encoding == "utf-8-sig":
                if prefix.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
                    encoding = "utf-32"
                elif prefix.startswith((b"\xff\xfe", b"\xfe\xff")):
                    encoding = "utf-16"
            with io.TextIOWrapper(
                io.BufferedReader(_BoundedReader(raw)), encoding=encoding, newline=""
            ) as stream:
                if fmt == "jsonl":
                    yield _jsonl_records(stream), None, fmt
                else:
                    sep = "\t" if fmt == "tsv" else delimiter
                    core._validate_delimiter(sep)
                    reader = csv.reader(stream, delimiter=sep, strict=True)
                    columns = next(reader, None)
                    if not columns:
                        raise core.ProbeFileError("CSV has no header row")
                    if any(len(field) > core.MAX_FIELD_CHARS for field in columns):
                        raise core.ProbeFileError("CSV field exceeds the safety limit")
                    if len(columns) != len(set(columns)):
                        raise core.ProbeFileError("CSV has duplicate column names")
                    yield _csv_records(reader, columns), columns, fmt
    except core.ProbeFileError:
        raise
    except csv.Error as exc:
        raise core.ProbeFileError(f"Malformed CSV: {exc}") from exc
    except (UnicodeError, LookupError) as exc:
        raise core.ProbeFileError(
            "Expected UTF-8 text or a supported BOM; use --encoding for legacy text"
        ) from exc
    except OSError as exc:
        raise core.ProbeFileError(f"Cannot read file: {exc}") from exc
