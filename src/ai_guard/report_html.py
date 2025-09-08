"""HTML report writer for AI-Guard."""

from typing import List, Dict, Any
from html import escape
from .report import GateResult

_BASE_CSS = """
body {
    font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    margin: 24px;
}
.badge {
    display:inline-block;
    padding:2px 8px;
    border-radius:12px;
    font-size:12px;
}
.badge.pass {
    background:#e6ffed;
    color:#05631f;
    border:1px solid #b6f7c6;
}
.badge.fail {
    background:#ffecec;
    color:#8a1111;
    border:1px solid #ffc1c1;
}
table {
    width:100%;
    border-collapse: collapse;
    margin-top: 12px;
}
th, td {
    text-align:left;
    padding:8px;
    border-bottom:1px solid #eee;
}
code {
    background:#f6f8fa;
    padding:2px 4px;
    border-radius:4px;
}
.finding-error { color:#8a1111; }
.finding-warning { color:#8a6a11; }
.finding-note { color:#555; }
"""


def write_html(
    report_path: str,
    gates: List[GateResult],
    findings: List[dict[str, str | int | None]],
) -> None:
    """Write an HTML report with gate summaries and findings.

    Args:
        report_path: Path to write the HTML file
        gates: List of gate results
        findings: List of findings as dictionaries with rule_id, level,
                 message, path, line
    """
    overall_pass = all(g.passed for g in gates)
    status = (
        f'<span class="badge {"pass" if overall_pass else "fail"}">'
        f'{"ALL GATES PASSED" if overall_pass else "GATES FAILED"}</span>'
    )

    gates_rows: List[str] = []
    for g in gates:
        status_badge = (
            '<span class="badge pass">PASS</span>'
            if g.passed
            else '<span class="badge fail">FAIL</span>'
        )
        gates_rows.append(
            f"<tr><td>{escape(g.name)}</td><td>{status_badge}</td>"
            f"<td>{escape(g.details or '')}</td></tr>"
        )
    gates_rows_str = "\n".join(gates_rows)

    def cls(level: str) -> str:
        return f"finding-{escape(str(level))}"

    findings_rows: List[str] = []
    for finding in findings:
        path = str(finding.get("path", ""))
        line = finding.get("line")
        level = str(finding.get("level", "note"))
        rule_id = str(finding.get("rule_id", ""))
        message = str(finding.get("message", ""))

        findings_rows.append(
            f"<tr>"
            f"<td><code>{escape(path)}:{str(line) if line else ''}</code></td>"
            f"<td class='{cls(level)}'>{escape(level.upper())}</td>"
            f"<td><code>{escape(rule_id)}</code></td>"
            f"<td>{escape(message)}</td>"
            f"</tr>"
        )
    findings_rows_str = "\n".join(findings_rows)

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>AI-Guard Report</title>
<style>{_BASE_CSS}</style></head>
<body>
<h1>AI-Guard Report</h1>
<p>{status}</p>

<h2>Gates</h2>
<table>
  <thead><tr><th>Gate</th><th>Status</th><th>Details</th></tr></thead>
  <tbody>{gates_rows_str}</tbody>
</table>

<h2>Findings</h2>
<table>
  <thead><tr><th>Location</th><th>Level</th><th>Rule</th><th>Message</th></tr></thead>
  <tbody>{findings_rows_str or '<tr><td colspan="4">No findings 🎉</td></tr>'}</tbody>
</table>
</body></html>
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)


class HTMLReportGenerator:
    """HTML report generator for AI-Guard quality gate results."""

    def __init__(self) -> None:
        """Initialize the HTML report generator."""

    def generate_html_report(
        self,
        results: List[GateResult],
        findings: List[Dict[str, Any]],
        output_path: str,
    ) -> None:
        """Generate an HTML report from gate results and findings.

        Args:
            results: List of gate results
            findings: List of findings dictionaries
            output_path: Path to write the HTML report
        """
        write_html(output_path, results, findings)

    def generate_summary_html(self, results: List[GateResult]) -> str:
        """Generate HTML summary from gate results.

        Args:
            results: List of gate results

        Returns:
            HTML summary as string
        """
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        html = f"""
        <div class="summary">
            <h2>Quality Gates Summary</h2>
            <p>Total: {len(results)}</p>
            <p>Passed: <span class="badge pass">{len(passed)}</span></p>
            <p>Failed: <span class="badge fail">{len(failed)}</span></p>
        </div>
        """

        if failed:
            html += "<div class='failed-gates'><h3>Failed Gates:</h3><ul>"
            for result in failed:
                html += f"<li>{result.name}: {result.details}</li>"
            html += "</ul></div>"

        return html
