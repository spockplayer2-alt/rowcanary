"""Validated, immutable options shared by Python and command-line integrations."""

from __future__ import annotations

import codecs
import json
from dataclasses import dataclass, fields
from pathlib import Path

from .core import ID_COLUMN, VALUE_COLUMN, ProbeFileError, _json_object, _validate_delimiter
from .formats import FORMATS
from .probes import EXTENDED, select_probes

MAX_CONFIG_BYTES = 64 * 1024


@dataclass(frozen=True)
class Config:
    """Reusable options; explicit CLI flags take precedence over loaded values."""

    file_format: str = "auto"
    encoding: str | None = None
    delimiter: str = ","
    id_column: str = ID_COLUMN
    value_column: str = VALUE_COLUMN
    probe_set: str = "default"
    custom_values: Path | None = None
    strict_order: bool = False
    schema_version: str = "1.0"

    def __post_init__(self):
        for name in ("file_format", "delimiter", "id_column", "value_column", "probe_set"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 255:
                raise ProbeFileError(
                    f"Configuration {name} must be non-empty text (up to 255 chars)"
                )
            try:
                value.encode("utf-8")
            except UnicodeError as exc:
                raise ProbeFileError(f"Configuration {name} must contain valid Unicode") from exc
        if self.schema_version != "1.0":
            raise ProbeFileError("Unsupported configuration schema_version")
        if self.file_format not in ("auto", *FORMATS):
            raise ProbeFileError("Unknown configuration file_format")
        _validate_delimiter(self.delimiter)
        if self.id_column == self.value_column:
            raise ProbeFileError("ID and value columns must be different")
        if type(self.strict_order) is not bool:
            raise ProbeFileError("Configuration strict_order must be a boolean")
        if self.encoding is not None:
            if not isinstance(self.encoding, str) or not self.encoding or len(self.encoding) > 64:
                raise ProbeFileError("Configuration encoding must be text or null")
            try:
                codecs.lookup(self.encoding)
            except (LookupError, ValueError) as exc:
                raise ProbeFileError("Unknown configuration encoding") from exc
        if self.probe_set not in ("default", "extended", "none") and not set(
            self.probe_set.split(",")
        ) <= {p.category for p in EXTENDED}:
            raise ProbeFileError("Unknown configuration probe_set or category")
        if self.custom_values is not None:
            if not isinstance(self.custom_values, (str, Path)) or not str(self.custom_values):
                raise ProbeFileError("Configuration custom_values must be a path or null")
            if "\x00" in str(self.custom_values):
                raise ProbeFileError("Configuration custom_values cannot contain NUL")
            object.__setattr__(self, "custom_values", Path(self.custom_values))

    def make_options(self) -> dict:
        """Keyword arguments for write_probes; generation uses fixed control columns."""
        return dict(
            file_format=self.file_format,
            encoding=self.encoding or "utf-8",
            delimiter=self.delimiter,
            probes=select_probes(self.probe_set, self.custom_values),
        )

    def check_options(self) -> dict:
        """Keyword arguments for check_file, with BOM-aware decoding by default."""
        options = self.make_options()
        options.update(
            encoding=self.encoding or "utf-8-sig",
            id_column=self.id_column,
            value_column=self.value_column,
            strict_order=self.strict_order,
        )
        return options


def load_config(path: Path) -> Config:
    """Read at most 64 KiB of UTF-8 JSON; resolve custom paths beside the config."""
    path = Path(path)
    try:
        with path.open("rb") as stream:
            data = stream.read(MAX_CONFIG_BYTES + 1)
        if len(data) > MAX_CONFIG_BYTES:
            raise ProbeFileError("Configuration exceeds the 64 KiB safety limit")
        document = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_json_object)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProbeFileError(f"Invalid configuration JSON: {exc}") from exc
    if not isinstance(document, dict) or document.keys() - {f.name for f in fields(Config)}:
        raise ProbeFileError("Configuration must be an object with known option names")
    config = Config(**document)
    if config.custom_values is not None:
        from dataclasses import replace

        config = replace(
            config, custom_values=(path.resolve().parent / config.custom_values).resolve()
        )
    return config
