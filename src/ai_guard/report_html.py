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
            f"<td><code>{escape(path)}:{str(line) if line is not None else ''}</code></td>"
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
            <p>Passed: {len(passed)} <span class="badge pass">{len(passed)}</span></p>
            <p>Failed: {len(failed)}{f' <span class="badge fail">{len(failed)}</span>'
                if failed else ''}</p>
        </div>
        """

        if passed:
            html += "<div class='passed-gates'><h3>Passed Gates:</h3><ul>"
            for result in passed:
                details = result.details or ""
                html += f"<li>{escape(result.name)}: {escape(details)}</li>"
            html += "</ul></div>"

        if failed:
            html += "<div class='failed-gates'><h3>Failed Gates:</h3><ul>"
            for result in failed:
                details = result.details or ""
                html += f"<li>{escape(result.name)}: {escape(details)}</li>"
            html += "</ul></div>"

        return html


def generate_html_report(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate an HTML report from analysis results.

    Args:
        analysis_results: Analysis results dictionary

    Returns:
        Dictionary with HTML report data
    """
    files_analyzed = analysis_results.get("files_analyzed", 0)
    total_issues = analysis_results.get("total_issues", 0)
    issues = analysis_results.get("issues", [])

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI-Guard Report</title>
        <style>{_BASE_CSS}</style>
    </head>
    <body>
        <h1>AI-Guard Analysis Report</h1>
        <p>Files analyzed: {files_analyzed}</p>
        <p>Total issues: {total_issues}</p>

        <h2>Issues</h2>
        <table>
            <thead>
                <tr><th>Type</th><th>Message</th><th>File</th><th>Line</th></tr>
            </thead>
            <tbody>
    """

    for issue in issues:
        issue_type = issue.get("type", "unknown")
        message = issue.get("message", "")
        file_path = issue.get("file", "")
        line = issue.get("line", "")

        html_content += f"""
                <tr>
                    <td class="finding-{issue_type}">{escape(issue_type.upper())}</td>
                    <td>{escape(message)}</td>
                    <td><code>{escape(file_path)}</code></td>
                    <td>{escape(str(line))}</td>
                </tr>
        """

    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    return {
        "success": True,
        "format": "html",
        "content": html_content,
        "files_analyzed": files_analyzed,
        "total_issues": total_issues,
    }


def format_html_summary(report_data: Dict[str, Any]) -> str:
    """Format a report summary as HTML.

    Args:
        report_data: Report data dictionary

    Returns:
        HTML formatted summary
    """
    files_count = report_data.get("files_analyzed", 0)
    issues_count = report_data.get("total_issues", 0)
    issues_by_type = report_data.get("issues_by_type", {})

    html = f"""
    <div class="summary">
        <h2>Analysis Summary</h2>
        <p>Files analyzed: {files_count}</p>
        <p>Total issues: {issues_count}</p>
    """

    for issue_type, count in issues_by_type.items():
        html += f"<p>{issue_type.title()}s: {count}</p>"

    html += "</div>"
    return html


def create_html_table(data: List[Dict[str, Any]], columns: List[str]) -> str:
    """Create an HTML table from data.

    Args:
        data: List of dictionaries containing row data
        columns: List of column names

    Returns:
        HTML table string
    """
    html = "<table>\n<thead>\n<tr>"

    for column in columns:
        html += f"<th>{escape(column.title())}</th>"

    html += "</tr>\n</thead>\n<tbody>\n"

    for row in data:
        html += "<tr>"
        for column in columns:
            value = row.get(column, "")
            html += f"<td>{escape(str(value))}</td>"
        html += "</tr>\n"

    html += "</tbody>\n</table>"
    return html


class HTMLReportGeneratorV2:
    """Enhanced HTML report generator class."""

    def __init__(self) -> None:
        """Initialize the HTML report generator."""
        pass

    def generate_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an HTML report.

        Args:
            analysis_results: Analysis results dictionary

        Returns:
            Dictionary with HTML report data
        """
        return generate_html_report(analysis_results)
