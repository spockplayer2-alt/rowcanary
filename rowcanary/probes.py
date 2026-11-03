"""Deterministic probe selection and validated, local custom scalar values."""

from __future__ import annotations

import json
import math
from pathlib import Path

from .core import MAX_FIELD_CHARS, MAX_ROWS, PROBES, Probe, ProbeFileError, _json_object, _read_text

EXTENDED = PROBES + (
    Probe("timestamp", "2025-08-09T01:02:03.123456+05:30", "dates", "Timestamp changed"),
    Probe("decimal-comma", "1.234,56", "numbers", "Locale decimal text changed"),
    Probe("precision", "1.234567890123456789", "numbers", "Decimal precision changed"),
    Probe("nfd", "cafe\u0301", "unicode", "Unicode normalization may have changed"),
    Probe("nbsp", "alpha\u00a0beta", "whitespace", "Non-breaking space changed"),
    Probe("crlf", "alpha\r\nbeta", "whitespace", "In-cell line breaks changed"),
    Probe("duplicate-plain", "normal text", "control", "Duplicate-value control changed"),
    Probe("false", "false", "keywords", "Boolean-like text changed"),
    Probe("null-lower", "null", "keywords", "Null-like text changed"),
    Probe("long-id", "0" + "1234567890" * 20, "identifiers", "Long identifier changed"),
    Probe("special", "a;b|c\\d/%?&<>", "punctuation", "Special characters changed"),
)


def validate_probes(probes) -> tuple[Probe, ...]:
    probes = tuple(probes)
    if not probes or len(probes) > MAX_ROWS:
        raise ProbeFileError("Probe set must contain between 1 and 100000 controls")
    seen = set()
    for p in probes:
        if not isinstance(p, Probe):
            raise ProbeFileError("Every probe must be a Probe instance")
        if (
            not isinstance(p.ident, str)
            or not p.ident
            or p.ident in seen
            or len(p.ident) > MAX_FIELD_CHARS
        ):
            raise ProbeFileError("Probe IDs must be unique, non-empty bounded text")
        seen.add(p.ident)
        if type(p.value) not in (str, int, float, bool, type(None)):
            raise ProbeFileError("Probe values must be JSON scalars")
        if isinstance(p.value, float) and not math.isfinite(p.value):
            raise ProbeFileError("Probe numbers must be finite")
        for value in (p.value, p.ident, p.category, p.reason):
            if isinstance(value, str):
                if len(value) > MAX_FIELD_CHARS:
                    raise ProbeFileError("Probe field exceeds the safety limit")
                try:
                    value.encode("utf-8")
                except UnicodeError as exc:
                    raise ProbeFileError("Probe text must contain valid Unicode") from exc
        if not isinstance(p.category, str) or not isinstance(p.reason, str):
            raise ProbeFileError("Probe category and reason must be text")
    return probes


def select_probes(
    probe_set: str = "default", custom_values: Path | None = None
) -> tuple[Probe, ...]:
    """Select default/extended/none or comma-separated categories, then append custom values."""
    if probe_set == "default":
        probes = PROBES
    elif probe_set == "extended":
        probes = EXTENDED
    elif probe_set == "none":
        probes = ()
    else:
        categories = set(probe_set.split(","))
        if not categories <= {p.category for p in EXTENDED}:
            raise ProbeFileError("Unknown probe set or category: " + probe_set)
        probes = tuple(p for p in EXTENDED if p.category in categories)
    if custom_values is not None:
        try:
            data = json.loads(_read_text(Path(custom_values)), object_pairs_hook=_json_object)
        except (ValueError, RecursionError) as exc:
            raise ProbeFileError("Invalid custom-values JSON: " + str(exc)) from exc
        if not isinstance(data, list) or len(data) > MAX_ROWS:
            raise ProbeFileError("Custom values must be a bounded JSON array")
        for item in data:
            if (
                not isinstance(item, dict)
                or set(item) - {"id", "value", "category", "reason"}
                or not {"id", "value"} <= item.keys()
            ):
                raise ProbeFileError(
                    "Each custom value requires id and value; category/reason are optional"
                )
            probes += (
                Probe(
                    item["id"],
                    item["value"],
                    item.get("category", "custom"),
                    item.get("reason", "Custom control changed"),
                ),
            )
    return validate_probes(probes)
