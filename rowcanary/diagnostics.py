"""Describe observable changes without asserting which application caused them."""

import re
import unicodedata
from datetime import datetime
from decimal import Decimal, DecimalException, ROUND_HALF_EVEN, localcontext


def value_type(value):
    from .core import _JsonNumber

    if isinstance(value, _JsonNumber):
        return "number"
    return {
        str: "string",
        bool: "boolean",
        int: "number",
        float: "number",
        type(None): "null",
        list: "array",
        dict: "object",
    }.get(type(value), "other")


def _dates(value):
    if len(value) > 10:
        return set()
    result = set()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            result.add(datetime.strptime(value, fmt).date())
        except ValueError:
            pass
    return result


def diagnose(before, after):
    kinds = []
    observations = []

    def add(kind, observation):
        kinds.append(kind)
        observations.append(observation)

    if value_type(before) != value_type(after):
        add("type-coercion", "The returned scalar type differs from the expected type.")
    if after is None and before is not None:
        add("null-conversion", "A non-null control was returned as null.")
    if isinstance(before, str) and isinstance(after, str):
        if before.split() == after.split():
            add(
                "whitespace-change",
                "Only whitespace differs, including possible line-break changes.",
            )
        if unicodedata.normalize("NFC", before) == unicodedata.normalize("NFC", after):
            add("unicode-normalization", "The strings have the same NFC normalization.")
        for encoding in ("latin1", "cp1252"):
            try:
                if before.encode("utf-8").decode(encoding) == after:
                    add(
                        "encoding-corruption",
                        "The returned text matches UTF-8 decoded with a legacy encoding.",
                    )
                    break
            except UnicodeError:
                pass
        if _dates(before) & _dates(after):
            add(
                "date-representation-change",
                "Both date-like strings can represent the same calendar date.",
            )
        if after and len(after) < len(before) and before.startswith(after):
            add("truncated", "The returned text is a shorter prefix of the expected text.")
        # Keep decimal analysis bounded; exact comparison above never depends on it.
        numeric = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
        if max(len(before), len(after)) <= 512 and all(
            re.fullmatch(numeric, v) for v in (before, after)
        ):
            try:
                with localcontext() as context:
                    context.prec = 1024
                    context.rounding = ROUND_HALF_EVEN
                    original, returned = Decimal(before), Decimal(after)
                    if original == returned:
                        kind = (
                            "leading-zero-removal"
                            if re.match(r"[+-]?0[0-9]", before) and len(after) < len(before)
                            else "numeric-representation-change"
                        )
                        add(
                            kind,
                            "The numeric-looking strings have equal decimal values but different text.",
                        )
                    elif returned.as_tuple().exponent > original.as_tuple().exponent:
                        add(
                            "precision-loss",
                            "The returned numeric-looking text has fewer decimal places and a different value.",
                        )
                        if (
                            original.quantize(Decimal(1).scaleb(returned.as_tuple().exponent))
                            == returned
                        ):
                            add(
                                "numeric-rounding",
                                "The value matches decimal half-even rounding to the returned precision; the cause is unconfirmed.",
                            )
            except (DecimalException, ValueError, OverflowError):
                pass
    return {
        "classifications": tuple(kinds or ["value-change"]),
        "observation": " ".join(observations)
        or "The returned value differs from the expected value.",
        "possible_causes": (
            "Import inference, export formatting or an intermediate edit may explain the change; this check cannot establish the cause.",
        ),
        "guidance": "Compare raw exports and import/export type, encoding, whitespace and precision settings using isolated controls.",
        "expected_type": value_type(before),
        "actual_type": value_type(after),
    }
