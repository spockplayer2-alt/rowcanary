# Security

RowCanary processes local control exports without sending them to remote services.
Text formats use Python's standard library; XLSX reading uses openpyxl and
defusedxml. It never evaluates formulas, executes input values or imports
user-provided code. The optional browser interface serves only IPv4 loopback;
Host/Origin/session-token checks and request limits apply. Do not expose it
through a tunnel or public port. This is a single-user local tool.

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

`check` is read-only. UTF-8/16/32 BOMs are detected by default; other text
encodings require an explicit option. Invalid bytes are rejected.
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

Reusable configuration is bounded to 64 KiB of UTF-8 JSON and rejects duplicate
or unknown keys and invalid option types. Custom-value paths are explicit local
inputs resolved beside the configuration, not sandboxed paths. Loading settings
does not execute code or write output. Use only intended local configuration.

The UI uses no external assets. Requests and temporary files are bounded; normal
completion removes temporary inputs. Forced termination can leave temporary
files. Same-user malware/processes and concurrent parent-directory replacement
are outside these protections. See [browser boundaries](docs/web-ui.md).

## Reporting a vulnerability

After the repository is published, use its **Security → Report a vulnerability**
private reporting option if enabled. If private reporting is unavailable, open
an issue requesting a private contact without including exploit details, private
data or credentials. Do not post sensitive details in public issues.
