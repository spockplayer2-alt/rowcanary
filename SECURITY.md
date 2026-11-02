# Security

RowCanary v0.1.0 processes local control exports with Python's standard library.
It makes no network calls and never evaluates formulas, executes input values
or imports user-provided code. This is an initial release, without a long-term
support commitment.

## Spreadsheet formula injection

The controls intentionally include formula-like text: `=1+1`, a phone number
starting with `+` and a signed value starting with `-`. Spreadsheet applications
may evaluate these strings. CSV quoting does not neutralize formulas. Use an
isolated test environment and inspect the application's import settings.

Do not put arbitrary formulas or real customer records in probe files.
RowCanary is not a sanitizer and a passing report does not prove that formulas
were never executed by another application. Formula tests in this repository
only parse and compare strings; they do not open a spreadsheet or run formulas.

## Files and untrusted input

`check` is read-only. Input must be UTF-8 (an initial UTF-8 BOM is supported).
Reads are bounded to 32 MiB; records and CSV field sizes are also limited. JSON
objects and diagnostics consume additional memory. See
[resource and parser limits](docs/limitations.md).

`make` exclusively creates the chosen output and refuses existing files and
symlinks. Do not write into directories concurrently controlled by another user
or process. Failed filesystem writes can leave an incomplete newly created
probe; regenerate under a new filename after resolving the failure.

Human-readable diagnostics escape terminal control characters; JSON reports
preserve values through JSON escapes. Reports may contain the exported values
and file path, so treat them as data when sharing logs.

## Reporting a vulnerability

After the repository is published, use its **Security → Report a vulnerability**
private reporting option if enabled. If private reporting is unavailable, open
an issue requesting a private contact without including exploit details, private
data or credentials. Do not post sensitive details in public issues.
