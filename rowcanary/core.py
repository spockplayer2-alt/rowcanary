"""Deterministic control samples for checking CSV/JSON data round trips."""

from __future__ import annotations

import csv
import io
import json
from decimal import Decimal, InvalidOperation
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ID_COLUMN = "_rowcanary_id"
VALUE_COLUMN = "_rowcanary_value"
MAX_BYTES = 32 * 1024 * 1024
MAX_ROWS = 100_000
MAX_FIELD_CHARS = 128 * 1024


@dataclass(frozen=True)
class Probe:
    ident: str
    value: str | int | float | bool | None
    category: str
    reason: str


PROBES: tuple[Probe, ...] = (
    Probe("plain", "normal text", "control", "Ordinary text changed"),
    Probe("zeroes", "00012345", "identifiers", "Leading zeroes may have been removed"),
    Probe("large-int", "12345678901234567890", "identifiers", "Long integer may have been rounded"),
    Probe(
        "scientific", "5E12", "identifiers", "Identifier may have been read as scientific notation"
    ),
    Probe("decimal", "19.9900", "numbers", "Decimal formatting or precision changed"),
    Probe("small-decimal", "0.000000123456789", "numbers", "Small decimal precision changed"),
    Probe("negative-zeroes", "-0009", "numbers", "Signed numeric-looking text changed"),
    Probe("phone", "+5511999990000", "identifiers", "International phone prefix or digits changed"),
    Probe("date-slash", "03/04/2025", "dates", "Ambiguous date-like text changed"),
    Probe("date-iso", "2025-08-09", "dates", "ISO date-like text changed"),
    Probe("time", "01:02:03", "dates", "Time-like text changed"),
    Probe("bool", "TRUE", "keywords", "Boolean-like text was coerced"),
    Probe("null", "NULL", "keywords", "Null-like text was coerced"),
    Probe("empty", "", "keywords", "Empty string changed or became null"),
    Probe("leading-space", "  leading", "whitespace", "Leading spaces were trimmed"),
    Probe("trailing-space", "trailing  ", "whitespace", "Trailing spaces were trimmed"),
    Probe("tab", "alpha\tbeta", "whitespace", "Embedded tab was changed"),
    Probe("newline", "line one\nline two", "whitespace", "Embedded newline was changed"),
    Probe("comma", "alpha,beta", "punctuation", "Embedded comma was changed"),
    Probe("quotes", 'He said "hello"', "punctuation", "Quotation marks were changed"),
    Probe("accent", "São Paulo / crème brûlée", "unicode", "Accented characters were changed"),
    Probe("nonlatin", "日本語 العربية", "unicode", "Non-Latin characters were changed"),
    Probe("emoji", "Cafe ☕ 🐤", "unicode", "Emoji or Unicode characters were changed"),
    Probe("formula", "=1+1", "formula", "Formula-like text was evaluated or rewritten"),
)


@dataclass(frozen=True)
class Issue:
    code: str
    ident: str
    reason: str
    expected: str | None = None
    actual: str | None = None
    severity: str = "error"
    classifications: tuple[str, ...] = ()
    observation: str = ""
    possible_causes: tuple[str, ...] = ()
    guidance: str = "Inspect the export settings and compare the control before and after."
    expected_type: str | None = None
    actual_type: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["classifications"] = list(self.classifications or (self.code,))
        result["possible_causes"] = list(self.possible_causes)
        result["observation"] = self.observation or self.reason
        return result


@dataclass(frozen=True)
class Report:
    passed: int
    total: int
    issues: tuple[Issue, ...]
    input_path: str
    observations: tuple[Issue, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.issues

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "ok": self.ok,
            "passed": self.passed,
            "total": self.total,
            "input": self.input_path,
            "issues": [issue.as_dict() for issue in self.issues],
            "observations": [issue.as_dict() for issue in self.observations],
        }


class ProbeFileError(ValueError):
    """The supplied file cannot be interpreted as an exported probe."""


def _read_bytes(path: Path) -> bytes:
    try:
        if not path.is_file():
            raise ProbeFileError(f"File does not exist: {path}")
        if path.stat().st_size > MAX_BYTES:
            raise ProbeFileError(f"File exceeds {MAX_BYTES // (1024 * 1024)} MiB safety limit")
        # A bounded binary read also protects against a file growing after stat.
        # Decoding bytes directly preserves CR, LF and CRLF inside CSV cells.
        with path.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ProbeFileError(f"File exceeds {MAX_BYTES // (1024 * 1024)} MiB safety limit")
        return data
    except OSError as exc:
        raise ProbeFileError(f"Cannot read file: {exc}") from exc


def _decode_text(data: bytes, encoding: str = "utf-8-sig") -> str:
    if encoding == "utf-8-sig":
        if data.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
            encoding = "utf-32"
        elif data.startswith((b"\xff\xfe", b"\xfe\xff")):
            encoding = "utf-16"
    try:
        return data.decode(encoding)
    except (UnicodeError, LookupError) as exc:
        raise ProbeFileError(
            "Expected UTF-8 text or a supported BOM; use --encoding for legacy text"
        ) from exc


def _read_text(path: Path, encoding: str = "utf-8-sig") -> str:
    return _decode_text(_read_bytes(path), encoding)


def _validate_delimiter(delimiter: str) -> None:
    if (
        not isinstance(delimiter, str)
        or len(delimiter) != 1
        or delimiter in '\r\n\0"'
        or "\ud800" <= delimiter <= "\udfff"
    ):
        raise ProbeFileError(
            "CSV delimiter must be one UTF-8 character other than CR, LF, NUL or double quote"
        )


def write_probes(
    path: Path,
    *,
    delimiter: str = ",",
    file_format: str = "auto",
    probes=PROBES,
    encoding: str = "utf-8",
) -> None:
    """Create probes exclusively; never overwrite an existing file."""
    from .formats import detect_format, encode_probes
    from .probes import validate_probes

    path = Path(path)
    selected = validate_probes(probes)
    data = encode_probes(selected, detect_format(path, file_format), delimiter, encoding)
    if len(data) > MAX_BYTES:
        raise ProbeFileError("Generated file exceeds the safety limit")
    # Some Windows runtimes follow dangling symlinks even in exclusive mode.
    if path.is_symlink():
        raise FileExistsError(f"File already exists: {path}")
    with path.open("xb") as stream:
        stream.write(data)


def _load_csv(text: str, *, delimiter: str) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
        columns = next(reader, None)
        if not columns:
            raise ProbeFileError("CSV has no header row")
        if any(len(field) > MAX_FIELD_CHARS for field in columns):
            raise ProbeFileError("CSV field exceeds the safety limit")
        if len(columns) != len(set(columns)):
            raise ProbeFileError("CSV has duplicate column names")
        rows = []
        for fields in reader:
            if len(rows) >= MAX_ROWS:
                raise ProbeFileError("CSV has too many rows")
            if any(len(field) > MAX_FIELD_CHARS for field in fields):
                raise ProbeFileError("CSV field exceeds the safety limit")
            if len(fields) > len(columns):
                raise ProbeFileError(f"CSV row {reader.line_num} has extra fields")
            # DictReader skips blank records, hiding rows added by an exporter.
            row = (
                {
                    name: fields[index] if index < len(fields) else None
                    for index, name in enumerate(columns)
                }
                if fields
                else {}
            )
            rows.append(row)
        return rows, columns
    except csv.Error as exc:
        raise ProbeFileError(f"Malformed CSV: {exc}") from exc


@dataclass(frozen=True, repr=False)
class _JsonNumber:
    """Keep a JSON numeric token exact without mistaking it for string data."""

    token: str

    def __repr__(self) -> str:
        return self.token


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProbeFileError(f"JSON has duplicate object key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(token: str) -> None:
    raise ProbeFileError(f"JSON contains invalid numeric constant: {token}")


def _load_json(text: str) -> list[dict[str, Any]]:
    try:
        document = json.loads(
            text,
            object_pairs_hook=_json_object,
            parse_int=_JsonNumber,
            parse_float=_JsonNumber,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise ProbeFileError(f"Malformed JSON: {exc.msg} at line {exc.lineno}") from exc
    except RecursionError as exc:
        raise ProbeFileError("JSON nesting is too deep") from exc
    if not isinstance(document, list):
        raise ProbeFileError("JSON must contain an array of objects")
    if len(document) > MAX_ROWS:
        raise ProbeFileError("JSON has too many rows")
    if any(not isinstance(item, dict) for item in document):
        raise ProbeFileError("Every JSON array item must be an object")
    pending = [document]
    while pending:
        value = pending.pop()
        if isinstance(value, str) and len(value) > MAX_FIELD_CHARS:
            raise ProbeFileError("JSON field exceeds the safety limit")
        if isinstance(value, dict):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return document


def check_file(
    path: Path,
    *,
    file_format: str = "auto",
    id_column: str = ID_COLUMN,
    value_column: str = VALUE_COLUMN,
    delimiter: str = ",",
    probes=PROBES,
    encoding: str = "utf-8-sig",
    strict_order: bool = False,
) -> Report:
    from .diagnostics import diagnose
    from .formats import load_rows
    from .probes import validate_probes

    if any(not isinstance(name, str) or not name for name in (id_column, value_column)):
        raise ProbeFileError("ID and value column names must be non-empty text")
    path = Path(path)
    probes = validate_probes(probes)
    if id_column == value_column:
        raise ProbeFileError("ID and value columns must be different")
    rows, columns, fmt = load_rows(path, file_format, delimiter, encoding)
    if columns is None:
        columns = [name for name in (id_column, value_column) if any(name in row for row in rows)]
    if (fmt in ("csv", "tsv", "xlsx") or rows) and (
        id_column not in columns or value_column not in columns
    ):
        raise ProbeFileError(
            f"Missing required columns: {id_column!r} and/or {value_column!r}; "
            "use --id-column and --value-column if the exporter renamed them"
        )
    expected = {probe.ident: probe for probe in probes}
    seen: set[str] = set()
    issues: list[Issue] = []
    order: list[str] = []
    passed = 0
    for index, row in enumerate(rows, start=2):
        if id_column not in row or value_column not in row:
            issues.append(
                Issue("missing-column", str(index), "Exported row lacks required columns")
            )
            continue
        ident = row[id_column]
        if not isinstance(ident, str):
            issues.append(
                Issue(
                    "invalid-id",
                    str(index),
                    "Probe identifier is no longer text",
                    actual=repr(ident),
                )
            )
            continue
        if ident in seen:
            issues.append(Issue("duplicate", ident, "Probe row occurs more than once"))
            continue
        seen.add(ident)
        if ident not in expected:
            issues.append(Issue("unexpected", ident, "Unexpected row was added"))
            continue
        probe = expected[ident]
        order.append(ident)
        actual_value = row[value_column]
        expected_value = (
            ("" if probe.value is None else str(probe.value))
            if fmt in ("csv", "tsv")
            else probe.value
        )
        if not _values_equal(actual_value, expected_value):
            actual_display = actual_value if isinstance(actual_value, str) else repr(actual_value)
            issues.append(
                Issue(
                    "changed",
                    ident,
                    probe.reason,
                    expected=_display_value(expected_value),
                    actual=actual_display,
                    **diagnose(expected_value, actual_value),
                )
            )
        else:
            passed += 1
    for ident, probe in expected.items():
        if ident not in seen:
            issues.append(
                Issue(
                    "missing", ident, "Probe row was dropped", expected=_display_value(probe.value)
                )
            )
    observations = ()
    if order != [ident for ident in expected if ident in seen]:
        reordered = Issue(
            "reordered",
            "rows",
            "Control rows appear in a different order",
            severity="error" if strict_order else "info",
            guidance="Disable sorting in the exporter if row order matters to your workflow.",
        )
        if strict_order:
            issues.append(reordered)
        else:
            observations = (reordered,)
    return Report(
        passed=passed,
        total=len(probes),
        issues=tuple(issues),
        input_path=str(path),
        observations=observations,
    )


def _display_value(value) -> str:
    return value if isinstance(value, str) else repr(value)


def _values_equal(actual, expected) -> bool:
    if isinstance(actual, _JsonNumber):
        if type(expected) not in (int, float):
            return False
        integer_token = not any(c in actual.token.lower() for c in ".e")
        if (type(expected) is int) != integer_token:
            return False
        try:
            return Decimal(actual.token) == Decimal(str(expected))
        except InvalidOperation:
            return False
    return type(actual) is type(expected) and actual == expected
