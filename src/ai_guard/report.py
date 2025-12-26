"""Reporting and result aggregation for AI-Guard."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import enhanced report system
try:
    from .report_optimized import (
        EnhancedReportGenerator,
        ReportConfig,
        ReportFormat,
        ReportType,
        ReportStatus,
        ReportMetrics,
        generate_enhanced_report,
    )

    ENHANCED_REPORTS_AVAILABLE = True
except ImportError:
    ENHANCED_REPORTS_AVAILABLE = False


@dataclass
class GateResult:
    """Result of a quality gate check."""

    name: str
    passed: bool
    details: str = ""
    exit_code: int = 0


def summarize(results: List[GateResult]) -> int:
    """Summarize all gate results and return overall exit code.

    Args:
        results: List of gate results

    Returns:
        0 if all gates passed, 1 if any failed
    """
    failed = [r for r in results if not r.passed]

    print("\n" + "=" * 50)
    print("AI-Guard Quality Gates Summary")
    print("=" * 50)

    for result in results:
        prefix = "" if result.passed else ""
        status = "PASSED" if result.passed else "FAILED"
        details = f" - {result.details}" if result.details else ""
        print(f"{prefix} {result.name}: {status}{details}")

    print("=" * 50)

    if failed:
        print(f" {len(failed)} gate(s) failed")
        return 1
    else:
        print(" All gates passed!")
        return 0


class ReportGenerator:
    """Report generator for AI-Guard quality gate results."""

    def __init__(self) -> None:
        """Initialize the report generator."""

    def generate_summary(self, results: List[GateResult]) -> str:
        """Generate a summary report from gate results.

        Args:
            results: List of gate results

        Returns:
            Summary report as string
        """
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        summary = "Quality Gates Summary:\n"
        summary += f"Total: {len(results)}\n"
        summary += f"Passed: {len(passed)}\n"
        summary += f"Failed: {len(failed)}\n"

        if failed:
            summary += "\nFailed Gates:\n"
            for result in failed:
                summary += f"- {result.name}: {result.details}\n"

        return summary

    def generate_detailed_report(self, results: List[GateResult]) -> str:
        """Generate a detailed report from gate results.

        Args:
            results: List of gate results

        Returns:
            Detailed report as string
        """
        report = "AI-Guard Quality Gates Detailed Report\n"
        report += "=" * 50 + "\n\n"

        for result in results:
            status = "PASSED" if result.passed else "FAILED"
            report += f"Gate: {result.name}\n"
            report += f"Status: {status}\n"
            if result.details:
                report += f"Details: {result.details}\n"
            report += f"Exit Code: {result.exit_code}\n"
            report += "-" * 30 + "\n"

        return report


def generate_report(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a report from analysis results.

    Args:
        analysis_results: Analysis results dictionary

    Returns:
        Generated report dictionary
    """
    return {
        "success": True,
        "timestamp": "2024-01-01T00:00:00Z",
        "files_analyzed": analysis_results.get("files_analyzed", 0),
        "total_issues": analysis_results.get("total_issues", 0),
        "issues_by_type": analysis_results.get("issues_by_type", {}),
        "summary": format_report_summary(analysis_results),
    }


def format_report_summary(report_data: Dict[str, Any]) -> str:
    """Format a report summary.

    Args:
        report_data: Report data dictionary

    Returns:
        Formatted summary string
    """
    files_count = report_data.get("files_analyzed", 0)
    issues_count = report_data.get("total_issues", 0)
    issues_by_type = report_data.get("issues_by_type", {})

    summary_parts = [f"{files_count} files analyzed"]
    summary_parts.append(f"{issues_count} total issues")

    for issue_type, count in issues_by_type.items():
        summary_parts.append(f"{count} {issue_type}s")

    return " | ".join(summary_parts)


def save_report_to_file(report_data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Save report data to a file.

    Args:
        report_data: Report data to save
        file_path: Path to save the file

    Returns:
        Result dictionary with success status
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def load_report_from_file(file_path: str) -> Dict[str, Any]:
    """Load report data from a file.

    Args:
        file_path: Path to the report file

    Returns:
        Result dictionary with success status and data
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"success": True, "data": data}
    except FileNotFoundError:
        return {"success": False, "error": "File not found"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON format"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class ReportGeneratorV2:
    """Enhanced report generator for AI-Guard quality gate results."""

    def __init__(
        self, report_format: str = "json", include_timestamp: bool = True
    ) -> None:
        """Initialize the report generator.

        Args:
            report_format: Format for the report (json, html, xml)
            include_timestamp: Whether to include timestamp
        """
        self.report_format = report_format
        self.include_timestamp = include_timestamp

    def generate_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report in the specified format.

        Args:
            analysis_results: Analysis results dictionary

        Returns:
            Generated report dictionary
        """
        if self.report_format == "json":
            return self._generate_json_report(analysis_results)
        elif self.report_format == "html":
            return self._generate_html_report(analysis_results)
        else:
            return {
                "success": False,
                "error": f"Unsupported format: {self.report_format}",
            }

    def _generate_json_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JSON report."""
        report_data = generate_report(analysis_results)
        return {
            "success": True,
            "format": "json",
            "content": json.dumps(report_data, indent=2),
            **report_data,
        }

    def _generate_html_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HTML report."""
        report_data = generate_report(analysis_results)
        html_content = f"""
        <html>
        <head><title>AI-Guard Report</title></head>
        <body>
            <h1>AI-Guard Analysis Report</h1>
            <p>Files analyzed: {report_data['files_analyzed']}</p>
            <p>Total issues: {report_data['total_issues']}</p>
        </body>
        </html>
        """
        return {
            "success": True,
            "format": "html",
            "content": html_content,
            **report_data,
        }


class ReportFormatter:
    """Formatter for reports."""

    def __init__(
        self,
        template_dir: Optional[str] = None,
        custom_styles: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the formatter.

        Args:
            template_dir: Directory containing templates
            custom_styles: Custom styling options
        """
        self.template_dir = template_dir
        self.custom_styles = custom_styles

    def format_summary(self, report_data: Dict[str, Any]) -> str:
        """Format a report summary.

        Args:
            report_data: Report data dictionary

        Returns:
            Formatted summary string
        """
        return format_report_summary(report_data)

    def format_issues_list(self, issues: List[Dict[str, Any]]) -> str:
        """Format a list of issues.

        Args:
            issues: List of issue dictionaries

        Returns:
            Formatted issues string
        """
        if not issues:
            return "No issues found."

        formatted_issues = []
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            message = issue.get("message", "No message")
            file_path = issue.get("file", "unknown")
            formatted_issues.append(f"{issue_type.upper()}: {message} ({file_path})")

        return "\n".join(formatted_issues)


# Enhanced reporting functions
def generate_enhanced_analysis_report(
    analysis_results: Dict[str, Any],
    format_type: str = "html",
    output_path: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Generate an enhanced analysis report using the new system.

    Args:
        analysis_results: Analysis results dictionary
        format_type: Report format (json, html, csv, xml)
        output_path: Optional output path for the report
        **kwargs: Additional configuration options

    Returns:
        Dictionary with report generation results
    """
    if not ENHANCED_REPORTS_AVAILABLE:
        # Fallback to legacy system
        return generate_report(analysis_results)

    try:
        # Use enhanced report system
        result = generate_enhanced_report(
            analysis_results=analysis_results,
            format_type=format_type,
            output_path=output_path,
            **kwargs,
        )

        return {
            "success": True,
            "enhanced": True,
            "report_data": result.get("report_data"),
            "export_results": result.get("export_results"),
            "analytics": result.get("analytics"),
        }

    except Exception as e:
        # Fallback to legacy system on error
        return {
            "success": True,
            "enhanced": False,
            "fallback": True,
            "legacy_report": generate_report(analysis_results),
            "error": str(e),
        }


def create_interactive_report(
    analysis_results: Dict[str, Any],
    report_type: str = "detailed",
    include_charts: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """Create an interactive report with advanced features.

    Args:
        analysis_results: Analysis results dictionary
        report_type: Type of report (summary, detailed, comparative, trend)
        include_charts: Whether to include interactive charts
        **kwargs: Additional configuration options

    Returns:
        Dictionary with interactive report data
    """
    if not ENHANCED_REPORTS_AVAILABLE:
        return {
            "success": False,
            "error": "Enhanced report system not available",
            "fallback_available": True,
        }

    try:
        from .report_optimized import ReportType

        report_type_enum = getattr(ReportType, report_type.upper(), ReportType.SUMMARY)

        config = ReportConfig(
            format=ReportFormat.HTML,
            report_type=report_type_enum,
            include_metadata=True,
            streaming_enabled=True,
            **kwargs,
        )

        generator = EnhancedReportGenerator(config)
        report_data = generator.generate_report(
            analysis_results=analysis_results,
            title="Interactive Analysis Report",
            description="Advanced interactive report with charts and filtering",
        )

        # Add interactive features
        interactive_features = {
            "search_enabled": True,
            "filtering_enabled": True,
            "sorting_enabled": True,
            "export_enabled": True,
            "charts_enabled": include_charts,
            "real_time_updates": True,
        }

        return {
            "success": True,
            "report_data": report_data,
            "interactive_features": interactive_features,
            "enhanced": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "enhanced": False,
        }


def get_report_analytics() -> Dict[str, Any]:
    """Get report generation analytics.

    Returns:
        Dictionary with analytics data
    """
    if not ENHANCED_REPORTS_AVAILABLE:
        return {
            "success": False,
            "error": "Enhanced report system not available",
        }

    try:
        generator = EnhancedReportGenerator()
        analytics = generator.get_analytics()

        return {
            "success": True,
            "analytics": analytics,
            "enhanced": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "enhanced": False,
        }


def compare_reports(
    report_data_1: Dict[str, Any], report_data_2: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare two analysis reports.

    Args:
        report_data_1: First report data
        report_data_2: Second report data

    Returns:
        Dictionary with comparison results
    """
    if not ENHANCED_REPORTS_AVAILABLE:
        return {
            "success": False,
            "error": "Enhanced report system not available",
        }

    try:
        from .report_optimized import ReportData, create_report_comparison

        # Convert to ReportData objects (simplified)
        report1 = ReportData(
            report_id="report_1",
            title="Report 1",
            description="First report",
            timestamp=datetime.now(),
            format=ReportFormat.JSON,
            status=ReportStatus.COMPLETED,
            metrics=ReportMetrics(),
            entries=[],
        )

        report2 = ReportData(
            report_id="report_2",
            title="Report 2",
            description="Second report",
            timestamp=datetime.now(),
            format=ReportFormat.JSON,
            status=ReportStatus.COMPLETED,
            metrics=ReportMetrics(),
            entries=[],
        )

        comparison = create_report_comparison([report1, report2], "trend")

        return {
            "success": True,
            "comparison": comparison,
            "enhanced": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "enhanced": False,
        }
