"""Deterministic, self-contained and escaped report exports."""

import json
from html import escape
from pathlib import Path

from .core import ProbeFileError


def html_report(reports):
    documents = [report.as_dict() if hasattr(report, "as_dict") else report for report in reports]
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">",
        "<title>RowCanary report</title><style>body{font:1rem system-ui;max-width:70rem;margin:2rem auto;padding:1rem;color:#182e2b;background:#fff}pre{white-space:pre-wrap;overflow-wrap:anywhere}article{border:1px solid #657973;padding:1rem;margin:1rem 0}dt{font-weight:bold}dd{margin:0 0 1rem}h2{overflow-wrap:anywhere}</style>",
        "<body><h1>RowCanary report</h1><p>Scope: only the provided control samples, not an entire real dataset. Possible causes are tentative.</p>",
    ]
    for report in documents:
        parts.append("<article><h2>" + escape(str(report.get("input", "Input"))) + "</h2>")
        if "error" in report:
            parts.append("<p>Error: " + escape(str(report["error"])) + "</p>")
        else:
            parts.append(
                "<p>"
                + ("PASS" if report["ok"] else "FAIL")
                + f" — {report['passed']}/{report['total']} controls preserved</p>"
            )
            for issue in report["issues"] + report["observations"]:
                parts.append("<h3>" + escape(issue["code"] + ": " + issue["ident"]) + "</h3><dl>")
                for label, key in (
                    ("Severity", "severity"),
                    ("Observation", "observation"),
                    ("Expected", "expected"),
                    ("Expected type", "expected_type"),
                    ("Actual", "actual"),
                    ("Actual type", "actual_type"),
                    ("Guidance", "guidance"),
                    ("Possible causes", "possible_causes"),
                ):
                    parts.append(
                        "<dt>"
                        + label
                        + "</dt><dd><pre>"
                        + escape(json.dumps(issue[key], ensure_ascii=True))
                        + "</pre></dd>"
                    )
                parts.append("</dl>")
        parts.append("</article>")
    return "".join(parts) + "</body></html>\n"


def export_report(path, reports, *, batch=False):
    path = Path(path)
    if path.is_symlink():
        raise ProbeFileError("Refusing to write a report through an existing symbolic link")
    documents = [report.as_dict() if hasattr(report, "as_dict") else report for report in reports]
    if path.suffix.lower() == ".html":
        content = html_report(documents)
    elif path.suffix.lower() == ".json":
        content = (
            json.dumps(
                {"schema_version": "1.0", "results": documents} if batch else documents[0],
                ensure_ascii=True,
                indent=2,
            )
            + "\n"
        )
    else:
        raise ProbeFileError("Report output must end in .html or .json")
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
