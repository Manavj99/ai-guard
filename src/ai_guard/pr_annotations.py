"""PR annotation system for AI-Guard to provide better GitHub integration."""

import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnnotationLevel(Enum):
    """Annotation levels for PR annotations."""

    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CodeIssue:
    """Represents a code quality issue found during analysis."""

    file_path: str
    line_number: int
    column: int
    severity: str  # error, warning, info
    message: str
    rule_id: str
    suggestion: Optional[str] = None
    fix_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert CodeIssue to dictionary format."""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "severity": self.severity,
            "message": self.message,
            "rule_id": self.rule_id,
            "suggestion": self.suggestion,
            "fix_code": self.fix_code,
        }


@dataclass
class PRAnnotation:
    """Represents a PR annotation to be added to GitHub."""

    file_path: str
    line_number: int
    message: str
    annotation_level: str  # notice, warning, failure
    title: Optional[str] = None
    raw_details: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    start_column: Optional[int] = None
    end_column: Optional[int] = None


@dataclass
class PRReviewSummary:
    """Summary of PR review with annotations and suggestions."""

    overall_status: str  # approved, changes_requested, commented
    summary: str
    annotations: List[PRAnnotation]
    suggestions: List[str]
    quality_score: float  # 0.0 to 1.0
    coverage_info: Optional[Dict[str, Any]] = None
    security_issues: Optional[List[str]] = None


class PRAnnotator:
    """Handles PR annotations and review generation."""

    def __init__(self, github_token: Optional[str] = None, repo: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPOSITORY")
        self.annotations: List[PRAnnotation] = []
        self.issues: List[CodeIssue] = []

    def add_issue(self, issue: CodeIssue) -> None:
        """Add a code quality issue for annotation."""
        self.issues.append(issue)

        # Convert to PR annotation
        annotation = self._issue_to_annotation(issue)
        if annotation:
            self.annotations.append(annotation)

    def _issue_to_annotation(self, issue: CodeIssue) -> Optional[PRAnnotation]:
        """Convert a code issue to a PR annotation."""
        # Map severity to annotation level
        level_mapping = {"error": "failure", "warning": "warning", "info": "notice"}

        annotation_level = level_mapping.get(issue.severity, "notice")

        # Create title
        title = f"{issue.rule_id}: {issue.message}"

        # Create detailed message
        message_parts = [issue.message]
        if issue.suggestion:
            message_parts.append(f"\n💡 **Suggestion:** {issue.suggestion}")
        if issue.fix_code:
            message_parts.append(f"\n🔧 **Fix:**\n```\n{issue.fix_code}\n```")

        message = "\n".join(message_parts)

        return PRAnnotation(
            file_path=issue.file_path,
            line_number=issue.line_number,
            message=message,
            annotation_level=annotation_level,
            title=title,
            start_line=issue.line_number,
            end_line=issue.line_number,
            start_column=issue.column,
            end_column=issue.column + 1,
        )

    def add_lint_issues(self, lint_results: List[Dict[str, Any]]) -> None:
        """Add linting issues from flake8/mypy/bandit results."""
        for result in lint_results:
            if isinstance(result, dict):
                issue = CodeIssue(
                    file_path=result.get("file", ""),
                    line_number=result.get("line", 0),
                    column=result.get("column", 0),
                    severity=result.get("severity", "warning"),
                    message=result.get("message", ""),
                    rule_id=result.get("rule", "unknown"),
                    suggestion=self._generate_lint_suggestion(result),
                )
                self.add_issue(issue)

    def _generate_lint_suggestion(self, lint_result: Dict[str, Any]) -> Optional[str]:
        """Generate helpful suggestions for lint issues."""
        rule_id = lint_result.get("rule", "").lower()

        suggestions = {
            "e501": "Consider breaking this long line into multiple lines",
            "e302": "Add two blank lines before class definition",
            "e303": "Remove extra blank lines",
            "f401": "Remove unused import or add 'noqa: F401' comment",
            "f841": "Remove unused variable or use underscore prefix",
            "w291": "Remove trailing whitespace",
            "w292": "Add newline at end of file",
            "w293": "Remove trailing whitespace on blank line",
        }

        for rule, suggestion in suggestions.items():
            if rule in rule_id:
                return suggestion

        return None

    def add_coverage_annotation(
        self, file_path: str, coverage_data: Dict[str, Any]
    ) -> None:
        """Add coverage-related annotations."""
        if not coverage_data:
            return

        coverage_percent = coverage_data.get("coverage_percent", 0)
        uncovered_lines = coverage_data.get("uncovered_lines", [])

        if coverage_percent < 80:
            # Add warning for low coverage
            annotation = PRAnnotation(
                file_path=file_path,
                line_number=1,
                message=(
                    f"⚠️ **Low Coverage Warning:** This file has {coverage_percent:.1f}% "
                    f"test coverage. Consider adding tests for uncovered lines."
                ),
                annotation_level="warning",
                title="Low Test Coverage",
                start_line=1,
                end_line=1,
            )
            self.annotations.append(annotation)

        # Add specific annotations for uncovered lines
        for line_num in uncovered_lines[:5]:  # Limit to first 5 uncovered lines
            annotation = PRAnnotation(
                file_path=file_path,
                line_number=line_num,
                message=(
                    "🔍 **Uncovered Line:** This line is not covered by tests. "
                    "Consider adding a test case."
                ),
                annotation_level="notice",
                title="Uncovered Code",
                start_line=line_num,
                end_line=line_num,
            )
            self.annotations.append(annotation)

    def add_security_annotation(self, security_issues: List[Dict[str, Any]]) -> None:
        """Add security-related annotations."""
        for issue in security_issues:
            if isinstance(issue, dict):
                severity = issue.get("severity", "medium")
                annotation_level = (
                    "failure" if severity in ["high", "critical"] else "warning"
                )

                annotation = PRAnnotation(
                    file_path=issue.get("file", ""),
                    line_number=issue.get("line", 0),
                    message=(
                        f"🛡️ **Security Issue ({severity.upper()}):** "
                        f"{issue.get('message', '')}"
                    ),
                    annotation_level=annotation_level,
                    title=f"Security: {issue.get('rule', 'Unknown')}",
                    start_line=issue.get("line", 0),
                    end_line=issue.get("line", 0),
                )
                self.annotations.append(annotation)

    def generate_review_summary(self) -> PRReviewSummary:
        """Generate a comprehensive PR review summary."""
        # Count issues by severity
        error_count = len([i for i in self.issues if i.severity == "error"])
        warning_count = len([i for i in self.issues if i.severity == "warning"])
        info_count = len([i for i in self.issues if i.severity == "info"])

        # Determine overall status
        if error_count > 0:
            overall_status = "changes_requested"
        elif warning_count > 5:
            overall_status = "changes_requested"
        elif warning_count > 0 or info_count > 0:
            overall_status = "commented"
        else:
            overall_status = "approved"

        # Calculate quality score (0.0 to 1.0)
        total_issues = len(self.issues)
        if total_issues == 0:
            quality_score = 1.0
        else:
            # Weight issues by severity
            weighted_score = error_count * 0.0 + warning_count * 0.5 + info_count * 0.8
            quality_score = max(0.0, 1.0 - (weighted_score / total_issues))

        # Generate summary
        summary_parts = []
        if error_count > 0:
            summary_parts.append(f"❌ {error_count} critical issues found")
        if warning_count > 0:
            summary_parts.append(f"⚠️ {warning_count} warnings")
        if info_count > 0:
            summary_parts.append(f"ℹ️ {info_count} suggestions")

        if not summary_parts:
            summary_parts.append("✅ All quality checks passed!")

        summary = " | ".join(summary_parts)

        # Generate suggestions
        suggestions = self._generate_suggestions()

        return PRReviewSummary(
            overall_status=overall_status,
            summary=summary,
            annotations=self.annotations,
            suggestions=suggestions,
            quality_score=quality_score,
        )

    def _generate_suggestions(self) -> List[str]:
        """Generate helpful suggestions based on found issues."""
        suggestions = []

        # Analyze common patterns
        error_rules = [i.rule_id for i in self.issues if i.severity == "error"]

        if "e501" in error_rules:
            suggestions.append(
                "Consider using a line length formatter like `black` or `autopep8`"
            )

        if "f401" in error_rules:
            suggestions.append("Run `isort` to organize imports and remove unused ones")

        if "f841" in error_rules:
            suggestions.append(
                "Use underscore prefix for intentionally unused variables (e.g., `_unused`)"
            )

        if len([i for i in self.issues if i.severity == "error"]) > 5:
            suggestions.append(
                "Consider running `black` to automatically format your code"
            )

        if not suggestions:
            suggestions.append("Great job! Keep up the good code quality practices.")

        return suggestions

    def create_github_annotations(self) -> List[Dict[str, Any]]:
        """Create GitHub annotations in the required format."""
        annotations = []

        for annotation in self.annotations:
            github_annotation = {
                "path": annotation.file_path,
                "start_line": annotation.start_line or annotation.line_number,
                "end_line": annotation.end_line or annotation.line_number,
                "annotation_level": annotation.annotation_level,
                "message": annotation.message,
            }

            if annotation.title:
                github_annotation["title"] = annotation.title

            if annotation.start_column and annotation.end_column:
                github_annotation["start_column"] = annotation.start_column
                github_annotation["end_column"] = annotation.end_column

            annotations.append(github_annotation)

        return annotations

    def create_review_comment(self, summary: PRReviewSummary) -> str:
        """Create a human-readable review comment."""
        comment_parts = [
            "## 🤖 AI-Guard Quality Review\n",
            f"**Status:** {summary.overall_status.replace('_', ' ').title()}\n",
            f"**Quality Score:** {summary.quality_score:.1%}\n\n",
            "### 📊 Summary\n",
            f"{summary.summary}\n\n",
        ]

        if summary.suggestions:
            comment_parts.extend(
                [
                    "### 💡 Suggestions\n",
                    *[f"- {suggestion}\n" for suggestion in summary.suggestions],
                    "\n",
                ]
            )

        if summary.annotations:
            comment_parts.extend(
                [
                    "### 🔍 Issues Found\n",
                    f"Total annotations: {len(summary.annotations)}\n\n",
                ]
            )

            # Group by file
            by_file: Dict[str, List[PRAnnotation]] = {}
            for annotation in summary.annotations:
                if annotation.file_path not in by_file:
                    by_file[annotation.file_path] = []
                by_file[annotation.file_path].append(annotation)

            for file_path, file_annotations in by_file.items():
                comment_parts.append(f"**{file_path}:**\n")
                for annotation in file_annotations[:3]:  # Show first 3 per file
                    emoji = {"failure": "❌", "warning": "⚠️", "notice": "ℹ️"}.get(
                        annotation.annotation_level, "ℹ️"
                    )
                    comment_parts.append(
                        f"- {emoji} Line {annotation.line_number}: {annotation.title}\n"
                    )
                if len(file_annotations) > 3:
                    comment_parts.append(
                        f"- ... and {len(file_annotations) - 3} more issues\n"
                    )
                comment_parts.append("\n")

        comment_parts.append("---\n")
        comment_parts.append("*This review was automatically generated by AI-Guard*")

        return "".join(comment_parts)

    def save_annotations(self, output_path: str) -> None:
        """Save annotations to a JSON file for external processing."""
        output_data = {
            "annotations": [self._annotation_to_dict(a) for a in self.annotations],
            "issues": [self._issue_to_dict(i) for i in self.issues],
            "summary": {
                "overall_status": self.generate_review_summary().overall_status,
                "summary": self.generate_review_summary().summary,
                "annotations": [
                    self._annotation_to_dict(a)
                    for a in self.generate_review_summary().annotations
                ],
                "suggestions": self.generate_review_summary().suggestions,
                "quality_score": self.generate_review_summary().quality_score,
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

    def _annotation_to_dict(self, annotation: PRAnnotation) -> Dict[str, Any]:
        """Convert annotation to dictionary for JSON serialization."""
        return {
            "file_path": annotation.file_path,
            "line_number": annotation.line_number,
            "message": annotation.message,
            "annotation_level": annotation.annotation_level,
            "title": annotation.title,
            "start_line": annotation.start_line,
            "end_line": annotation.end_line,
            "start_column": annotation.start_column,
            "end_column": annotation.end_column,
        }

    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """Convert issue to dictionary for JSON serialization."""
        return {
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "column": issue.column,
            "severity": issue.severity,
            "message": issue.message,
            "rule_id": issue.rule_id,
            "suggestion": issue.suggestion,
            "fix_code": issue.fix_code,
        }


def create_pr_annotations(
    lint_output: Optional[str] = None,
    bandit_output: Optional[str] = None,
    mypy_output: Optional[str] = None,
    coverage_output: Optional[str] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """Create PR annotations from various analysis outputs.

    Args:
        lint_output: Output from linting tools
        bandit_output: Output from security scanning
        mypy_output: Output from type checking
        coverage_output: Output from coverage tools
        output_file: Optional file to write results to

    Returns:
        Dictionary containing annotations and summary
    """
    annotator = PRAnnotator()

    # Process lint output
    if lint_output:
        # Parse lint output and add issues
        # This is a simplified implementation
        lint_issues = parse_lint_output(lint_output)
        lint_dicts = [issue.to_dict() for issue in lint_issues]
        annotator.add_lint_issues(lint_dicts)

    # Process bandit output
    if bandit_output:
        # Parse security output and add issues
        security_issues = parse_bandit_output(bandit_output)
        security_dicts = [issue.to_dict() for issue in security_issues]
        annotator.add_security_annotation(security_dicts)

    # Process mypy output
    if mypy_output:
        # Parse type checking output and add issues
        type_issues = parse_mypy_output(mypy_output)
        type_dicts = [issue.to_dict() for issue in type_issues]
        annotator.add_lint_issues(type_dicts)

    # Process coverage output
    if coverage_output:
        # Parse coverage output and add annotations
        coverage_data = _parse_coverage_output(coverage_output)
        for file_path, coverage in coverage_data.items():
            annotator.add_coverage_annotation(file_path, coverage)

    # Generate summary
    summary = annotator.generate_review_summary()

    # Prepare result
    result = {
        "annotations": [
            annotator._annotation_to_dict(a) for a in annotator.annotations
        ],
        "issues": [annotator._issue_to_dict(i) for i in annotator.issues],
        "summary": {
            "overall_status": summary.overall_status,
            "summary": summary.summary,
            "quality_score": summary.quality_score,
            "suggestions": summary.suggestions,
        },
    }

    # Write to file if requested
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write output file: {e}")
            result["error"] = f"Failed to write output file: {e}"

    return result


def write_annotations_file(annotations: List[Dict[str, Any]], output_path: str) -> bool:
    """Write annotations to a file.

    Args:
        annotations: List of annotation dictionaries
        output_path: Path to write the file to

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(annotations, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to write annotations file: {e}")
        return False


def _parse_coverage_output(coverage_output: str) -> Dict[str, Dict[str, Any]]:
    """Parse coverage output into structured format."""
    # Simplified parser for coverage output
    coverage_data = {}
    lines = coverage_output.split("\n")

    for line in lines:
        if "TOTAL" in line and "%" in line:
            # Extract overall coverage percentage
            try:
                percent_str = line.split("%")[0].split()[-1]
                percent = float(percent_str)
                coverage_data["overall"] = {
                    "coverage_percent": percent,
                    "uncovered_lines": [],
                }
            except (ValueError, IndexError):
                pass

    return coverage_data


def parse_lint_output(lint_output: str) -> List[CodeIssue]:
    """Parse lint output and return list of CodeIssue objects.

    Args:
        lint_output: Raw output from linting tools

    Returns:
        List of CodeIssue objects
    """
    issues = []
    lines = lint_output.split("\n")

    for line in lines:
        if ":" in line and any(rule in line for rule in ["E", "W", "F"]):
            parts = line.split(":")
            if len(parts) >= 3:
                file_path = parts[0]
                line_num = int(parts[1]) if parts[1].isdigit() else 0
                message = ":".join(parts[2:]).strip()

                # Extract rule ID if present
                rule_id = "unknown"
                for part in parts[2:]:
                    if any(rule in part for rule in ["E", "W", "F"]):
                        rule_parts = part.split()
                        for word in rule_parts:
                            if any(rule in word for rule in ["E", "W", "F"]):
                                rule_id = word
                                break
                        break

                issues.append(
                    CodeIssue(
                        file_path=file_path,
                        line_number=line_num,
                        column=0,
                        severity="warning",
                        message=message,
                        rule_id=rule_id,
                    )
                )

    return issues


def parse_mypy_output(mypy_output: str) -> List[CodeIssue]:
    """Parse mypy output and return list of CodeIssue objects.

    Args:
        mypy_output: Raw output from mypy

    Returns:
        List of CodeIssue objects
    """
    issues = []
    lines = mypy_output.split("\n")

    for line in lines:
        if ":" in line and ("error:" in line or "note:" in line):
            parts = line.split(":")
            if len(parts) >= 3:
                file_path = parts[0]
                line_num = int(parts[1]) if parts[1].isdigit() else 0
                message = ":".join(parts[2:]).strip()

                severity = "error" if "error:" in line else "info"

                issues.append(
                    CodeIssue(
                        file_path=file_path,
                        line_number=line_num,
                        column=0,
                        severity=severity,
                        message=message,
                        rule_id="mypy",
                    )
                )

    return issues


def parse_bandit_output(bandit_output: str) -> List[CodeIssue]:
    """Parse bandit output and return list of CodeIssue objects.

    Args:
        bandit_output: Raw output from bandit

    Returns:
        List of CodeIssue objects
    """
    issues = []
    lines = bandit_output.split("\n")

    for line in lines:
        if ">> Issue:" in line:
            # Extract security issue information
            parts = line.split(">> Issue:")
            if len(parts) >= 2:
                issue_info = parts[1].strip()
                # Parse file and line if available
                if ":" in issue_info:
                    file_part, message = issue_info.split(":", 1)
                    if ":" in file_part:
                        file_path, line_str = file_part.rsplit(":", 1)
                        try:
                            line_num = int(line_str)
                        except ValueError:
                            line_num = 0
                    else:
                        file_path = file_part
                        line_num = 0

                    issues.append(
                        CodeIssue(
                            file_path=file_path.strip(),
                            line_number=line_num,
                            column=0,
                            severity="medium",
                            message=message.strip(),
                            rule_id="security_scan",
                        )
                    )

    return issues


def create_github_annotation(issue: CodeIssue) -> Dict[str, Any]:
    """Create a GitHub annotation from a CodeIssue.

    Args:
        issue: CodeIssue object

    Returns:
        GitHub annotation dictionary
    """
    # Map severity to annotation level
    level_mapping = {
        "error": "failure",
        "warning": "warning",
        "info": "notice",
        "medium": "warning",
    }

    annotation_level = level_mapping.get(issue.severity, "notice")

    annotation = {
        "path": issue.file_path,
        "start_line": issue.line_number,
        "end_line": issue.line_number,
        "annotation_level": annotation_level,
        "message": format_annotation_message(issue),
        "title": f"{issue.rule_id}: {issue.message}",
    }

    if issue.column > 0:
        annotation["start_column"] = issue.column
        annotation["end_column"] = issue.column + 1

    return annotation


def format_annotation_message(issue: CodeIssue) -> str:
    """Format a CodeIssue into a readable annotation message.

    Args:
        issue: CodeIssue object

    Returns:
        Formatted message string
    """
    message_parts = [issue.message]

    if issue.suggestion:
        message_parts.append(f"\n💡 **Suggestion:** {issue.suggestion}")

    if issue.fix_code:
        message_parts.append(f"\n🔧 **Fix:**\n```\n{issue.fix_code}\n```")

    return "\n".join(message_parts)


def main() -> None:
    """Main entry point for PR annotation system."""
    import argparse

    parser = argparse.ArgumentParser(description="PR annotation system for AI-Guard")
    parser.add_argument(
        "--input", required=True, help="Input file with analysis results"
    )
    parser.add_argument(
        "--output", default="annotations.json", help="Output file for annotations"
    )
    parser.add_argument("--github-token", help="GitHub token for API access")
    parser.add_argument("--repo", help="GitHub repository (owner/repo)")

    args = parser.parse_args()

    # Initialize annotator
    annotator = PRAnnotator(github_token=args.github_token, repo=args.repo)

    # Load input data
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            input_data = json.load(f)

        # Process different types of results
        if "lint_results" in input_data:
            annotator.add_lint_issues(input_data["lint_results"])

        if "coverage_data" in input_data:
            for file_path, coverage in input_data["coverage_data"].items():
                annotator.add_coverage_annotation(file_path, coverage)

        if "security_issues" in input_data:
            annotator.add_security_annotation(input_data["security_issues"])

        # Generate summary
        summary = annotator.generate_review_summary()

        # Save annotations
        annotator.save_annotations(args.output)

        # Print summary
        print("PR Review Summary:")
        print(f"Status: {summary.overall_status}")
        print(f"Quality Score: {summary.quality_score:.1%}")
        print(f"Annotations: {len(summary.annotations)}")
        print(f"Output saved to: {args.output}")

        # Print review comment
        print("\n" + "=" * 50)
        print("Review Comment:")
        print("=" * 50)
        print(annotator.create_review_comment(summary))

    except Exception as e:
        print(f"Error processing input: {e}")
        exit(1)


if __name__ == "__main__":
    main()
