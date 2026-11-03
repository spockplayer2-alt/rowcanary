# RowCanary release notes

See [CHANGELOG](../CHANGELOG.md) for version-specific changes and the
[public releases](https://github.com/spockplayer2-alt/rowcanary/releases) for
verified wheel, sdist, source ZIP and SHA256SUMS.txt attachments.

RowCanary provides exact control comparisons in CSV, TSV, JSON, JSONL and XLSX,
versioned JSON/standalone HTML reports, batch checks, a local browser interface
and a reusable Python/configuration API. Python 3.10–3.14 is supported. Runtime
XLSX reading uses openpyxl and defusedxml; the CLI/UI adds no web framework.

Install v1.0.0 from [PyPI](https://pypi.org/project/rowcanary/1.0.0/) with
`python -m pip install rowcanary`.

Read [quick start](quickstart.md), [verification](verification.md) and
[limitations](limitations.md). Native Excel text and automatic CSV profiles
changed controls; other applications remain unverified. A pass covers the
provided controls only. Formula-like probes belong in isolated test data.
