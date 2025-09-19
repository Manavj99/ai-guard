"""Advanced security scanner for AI Guard."""

import ast
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..exceptions import SecurityError
from ..utils.subprocess_runner import run_command_safe


class SeverityLevel(Enum):
    """Security severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityVulnerability:
    """Security vulnerability information."""

    rule_id: str
    severity: SeverityLevel
    message: str
    file_path: str
    line_number: int
    column: int
    code_snippet: str
    description: str
    remediation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


@dataclass
class DependencyVulnerability:
    """Dependency vulnerability information."""

    package_name: str
    version: str
    vulnerability_id: str
    severity: SeverityLevel
    description: str
    cve_id: Optional[str] = None
    fixed_version: Optional[str] = None


class AdvancedSecurityScanner:
    """Advanced security scanner with multiple detection methods."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security scanner.

        Args:
            config: Scanner configuration
        """
        self.config = config or {}
        self.vulnerabilities: List[SecurityVulnerability] = []
        self.dependency_vulnerabilities: List[DependencyVulnerability] = []

        # Security patterns
        self.security_patterns = self._load_security_patterns()

        # Dangerous functions and modules
        self.dangerous_functions = {
            "eval",
            "exec",
            "compile",
            "__import__",
            "getattr",
            "setattr",
            "delattr",
            "hasattr",
            "globals",
            "locals",
            "vars",
            "dir",
        }

        self.dangerous_modules = {
            "os",
            "subprocess",
            "sys",
            "pickle",
            "marshal",
            "shelve",
            "dbm",
            "sqlite3",
            "socket",
            "urllib",
            "http",
            "ftplib",
        }

    def _load_security_patterns(self) -> Dict[str, List[str]]:
        """Load security patterns for detection."""
        return {
            "sql_injection": [
                r"SELECT.*\+.*%s",
                r"INSERT.*\+.*%s",
                r"UPDATE.*\+.*%s",
                r"DELETE.*\+.*%s",
                r"execute.*%s",
                r"cursor\.execute.*%s",
            ],
            "xss": [
                r"innerHTML\s*=",
                r"outerHTML\s*=",
                r"document\.write\(",
                r"eval\(",
                r"setTimeout\(",
                r"setInterval\(",
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\\\",
                r"%2e%2e%2f",
                r"%2e%2e%5c",
                r"\.\.%2f",
                r"\.\.%5c",
            ],
            "command_injection": [
                r"os\.system\(",
                r"subprocess\.call\(",
                r"subprocess\.run\(",
                r"subprocess\.Popen\(",
                r"os\.popen\(",
                r"commands\.getoutput\(",
            ],
            "hardcoded_secrets": [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'private_key\s*=\s*["\'][^"\']+["\']',
            ],
            "weak_crypto": [
                r"md5\(",
                r"sha1\(",
                r"DES\.",
                r"RC4",
                r"random\.random\(",
                r"random\.randint\(",
            ],
        }

    def scan_file(self, file_path: str) -> List[SecurityVulnerability]:
        """Scan a single file for security vulnerabilities.

        Args:
            file_path: Path to file to scan

        Returns:
            List of security vulnerabilities
        """
        vulnerabilities = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Pattern-based scanning
            vulnerabilities.extend(self._scan_patterns(file_path, content))

            # AST-based scanning
            vulnerabilities.extend(self._scan_ast(file_path, content))

            # Hardcoded secrets scanning
            vulnerabilities.extend(self._scan_hardcoded_secrets(file_path, content))

        except Exception as e:
            raise SecurityError(f"Failed to scan file {file_path}: {e}")

        return vulnerabilities

    def _scan_patterns(
        self, file_path: str, content: str
    ) -> List[SecurityVulnerability]:
        """Scan content using security patterns."""
        vulnerabilities = []

        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_number = content[: match.start()].count("\n") + 1
                    column = match.start() - content.rfind("\n", 0, match.start()) - 1

                    vulnerability = SecurityVulnerability(
                        rule_id=f"SECURITY_{category.upper()}",
                        severity=self._get_severity_for_category(category),
                        message=f"Potential {category.replace('_', ' ')} vulnerability detected",
                        file_path=file_path,
                        line_number=line_number,
                        column=column,
                        code_snippet=match.group(),
                        description=(
                            f"Detected potential {category.replace('_', ' ')} vulnerability"
                        ),
                        remediation=self._get_remediation_for_category(category),
                    )
                    vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _scan_ast(self, file_path: str, content: str) -> List[SecurityVulnerability]:
        """Scan content using AST analysis."""
        vulnerabilities = []

        try:
            tree = ast.parse(content)
            visitor = SecurityASTVisitor(file_path)
            visitor.visit(tree)
            vulnerabilities.extend(visitor.vulnerabilities)
        except SyntaxError:
            # Skip files with syntax errors
            pass

        return vulnerabilities

    def _scan_hardcoded_secrets(
        self, file_path: str, content: str
    ) -> List[SecurityVulnerability]:
        """Scan for hardcoded secrets."""
        vulnerabilities = []

        # Common secret patterns
        secret_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', "password"),
            (r'secret\s*=\s*["\']([^"\']+)["\']', "secret"),
            (r'api_key\s*=\s*["\']([^"\']+)["\']', "api_key"),
            (r'token\s*=\s*["\']([^"\']+)["\']', "token"),
            (r'private_key\s*=\s*["\']([^"\']+)["\']', "private_key"),
        ]

        for pattern, secret_type in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_number = content[: match.start()].count("\n") + 1
                column = match.start() - content.rfind("\n", 0, match.start()) - 1

                vulnerability = SecurityVulnerability(
                    rule_id=f"HARDCODED_{secret_type.upper()}",
                    severity=SeverityLevel.HIGH,
                    message=f"Hardcoded {secret_type} detected",
                    file_path=file_path,
                    line_number=line_number,
                    column=column,
                    code_snippet=match.group(),
                    description=f"Hardcoded {secret_type} found in source code",
                    remediation=(
                        f"Move {secret_type} to environment variables or "
                        "secure configuration"
                    ),
                )
                vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _get_severity_for_category(self, category: str) -> SeverityLevel:
        """Get severity level for vulnerability category."""
        severity_map = {
            "sql_injection": SeverityLevel.HIGH,
            "xss": SeverityLevel.HIGH,
            "path_traversal": SeverityLevel.HIGH,
            "command_injection": SeverityLevel.CRITICAL,
            "hardcoded_secrets": SeverityLevel.HIGH,
            "weak_crypto": SeverityLevel.MEDIUM,
        }
        return severity_map.get(category, SeverityLevel.MEDIUM)

    def _get_remediation_for_category(self, category: str) -> str:
        """Get remediation advice for vulnerability category."""
        remediation_map = {
            "sql_injection": "Use parameterized queries or prepared statements",
            "xss": "Sanitize user input and use proper output encoding",
            "path_traversal": "Validate and sanitize file paths",
            "command_injection": "Avoid shell execution, use subprocess with proper arguments",
            "hardcoded_secrets": "Use environment variables or secure configuration management",
            "weak_crypto": (
                "Use strong cryptographic algorithms and proper random number generation"
            ),
        }
        return remediation_map.get(category, "Review and fix the security issue")

    def scan_dependencies(
        self, requirements_file: str
    ) -> List[DependencyVulnerability]:
        """Scan dependencies for known vulnerabilities.

        Args:
            requirements_file: Path to requirements file

        Returns:
            List of dependency vulnerabilities
        """
        vulnerabilities = []

        try:
            # Use safety to check for known vulnerabilities
            result = run_command_safe(
                ["safety", "check", "--json", "--file", requirements_file]
            )

            if result["success"] and result["stdout"]:
                safety_data = json.loads(result["stdout"])

                for vuln in safety_data:
                    vulnerability = DependencyVulnerability(
                        package_name=vuln.get("package_name", ""),
                        version=vuln.get("installed_version", ""),
                        vulnerability_id=vuln.get("vulnerability_id", ""),
                        severity=self._parse_severity(vuln.get("severity", "medium")),
                        description=vuln.get("advisory", ""),
                        cve_id=vuln.get("cve", ""),
                        fixed_version=vuln.get("fixed_version"),
                    )
                    vulnerabilities.append(vulnerability)

        except Exception as e:
            raise SecurityError(f"Failed to scan dependencies: {e}")

        return vulnerabilities

    def _parse_severity(self, severity_str: str) -> SeverityLevel:
        """Parse severity string to SeverityLevel enum."""
        severity_map = {
            "critical": SeverityLevel.CRITICAL,
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW,
            "info": SeverityLevel.INFO,
        }
        return severity_map.get(severity_str.lower(), SeverityLevel.MEDIUM)

    def get_security_score(self) -> float:
        """Calculate security score based on vulnerabilities.

        Returns:
            Security score (0-100)
        """
        if not self.vulnerabilities:
            return 100.0

        total_penalty = 0
        for vuln in self.vulnerabilities:
            penalty_map = {
                SeverityLevel.CRITICAL: 25,
                SeverityLevel.HIGH: 15,
                SeverityLevel.MEDIUM: 10,
                SeverityLevel.LOW: 5,
                SeverityLevel.INFO: 1,
            }
            total_penalty += penalty_map.get(vuln.severity, 10)

        score = max(0, 100 - total_penalty)
        return score

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report.

        Returns:
            Security report dictionary
        """
        severity_counts = {}
        for vuln in self.vulnerabilities:
            severity = vuln.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_vulnerabilities": len(self.vulnerabilities),
            "severity_counts": severity_counts,
            "security_score": self.get_security_score(),
            "vulnerabilities": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity.value,
                    "message": v.message,
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "description": v.description,
                    "remediation": v.remediation,
                }
                for v in self.vulnerabilities
            ],
            "dependency_vulnerabilities": [
                {
                    "package_name": v.package_name,
                    "version": v.version,
                    "vulnerability_id": v.vulnerability_id,
                    "severity": v.severity.value,
                    "description": v.description,
                    "cve_id": v.cve_id,
                    "fixed_version": v.fixed_version,
                }
                for v in self.dependency_vulnerabilities
            ],
        }


class SecurityASTVisitor(ast.NodeVisitor):
    """AST visitor for security analysis."""

    def __init__(self, file_path: str):
        """Initialize AST visitor.

        Args:
            file_path: Path to file being analyzed
        """
        self.file_path = file_path
        self.vulnerabilities: List[SecurityVulnerability] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls."""
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in {"eval", "exec", "compile"}:
                self._add_vulnerability(
                    f"DANGEROUS_FUNCTION_{func_name.upper()}",
                    SeverityLevel.HIGH,
                    f"Dangerous function '{func_name}' called",
                    node.lineno,
                    node.col_offset,
                    f"{func_name}()",
                    f"Function '{func_name}' can execute arbitrary code",
                    f"Avoid using '{func_name}', use safer alternatives",
                )

        # Check for subprocess calls without proper arguments
        if isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr in {"call", "run", "Popen"}
            ):

                # Check if shell=True is used
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(
                        keyword.value, ast.Constant
                    ):
                        if keyword.value.value is True:
                            self._add_vulnerability(
                                "SUBPROCESS_SHELL_TRUE",
                                SeverityLevel.HIGH,
                                "subprocess called with shell=True",
                                node.lineno,
                                node.col_offset,
                                "subprocess.call(shell=True)",
                                "Using shell=True can lead to command injection",
                                "Use shell=False and pass arguments as list",
                            )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            if alias.name in {"pickle", "marshal", "shelve"}:
                self._add_vulnerability(
                    f"DANGEROUS_MODULE_{alias.name.upper()}",
                    SeverityLevel.MEDIUM,
                    f"Dangerous module '{alias.name}' imported",
                    node.lineno,
                    node.col_offset,
                    f"import {alias.name}",
                    f"Module '{alias.name}' can be used for code execution",
                    f"Review usage of '{alias.name}' module",
                )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements."""
        if node.module in {"pickle", "marshal", "shelve"}:
            self._add_vulnerability(
                f"DANGEROUS_MODULE_{node.module.upper()}",
                SeverityLevel.MEDIUM,
                f"Dangerous module '{node.module}' imported",
                node.lineno,
                node.col_offset,
                f"from {node.module} import ...",
                f"Module '{node.module}' can be used for code execution",
                f"Review usage of '{node.module}' module",
            )

    def _add_vulnerability(
        self,
        rule_id: str,
        severity: SeverityLevel,
        message: str,
        line_number: int,
        column: int,
        code_snippet: str,
        description: str,
        remediation: str,
    ) -> None:
        """Add vulnerability to list."""
        vulnerability = SecurityVulnerability(
            rule_id=rule_id,
            severity=severity,
            message=message,
            file_path=self.file_path,
            line_number=line_number,
            column=column,
            code_snippet=code_snippet,
            description=description,
            remediation=remediation,
        )
        self.vulnerabilities.append(vulnerability)
