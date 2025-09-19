"""Tests for AI Guard security scanner."""

import tempfile
import os
import pytest
from src.ai_guard.security.advanced_scanner import (
    AdvancedSecurityScanner,
    SecurityVulnerability,
    DependencyVulnerability,
    SeverityLevel
)


class TestAdvancedSecurityScanner:
    """Test AdvancedSecurityScanner class."""

    def test_scanner_initialization(self):
        """Test scanner initialization."""
        scanner = AdvancedSecurityScanner()
        
        assert scanner.config == {}
        assert scanner.vulnerabilities == []
        assert scanner.dependency_vulnerabilities == []
        assert 'sql_injection' in scanner.security_patterns

    def test_scan_file_sql_injection(self):
        """Test scanning file for SQL injection."""
        scanner = AdvancedSecurityScanner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('query = "SELECT * FROM users WHERE id = " + user_id\n')
            temp_file = f.name
        
        try:
            vulnerabilities = scanner.scan_file(temp_file)
            
            # Should find SQL injection vulnerability
            sql_vulns = [v for v in vulnerabilities if 'SQL_INJECTION' in v.rule_id]
            assert len(sql_vulns) > 0
            
            vuln = sql_vulns[0]
            assert vuln.severity == SeverityLevel.HIGH
            assert vuln.file_path == temp_file
        
        finally:
            os.unlink(temp_file)

    def test_scan_file_safe_code(self):
        """Test scanning safe code."""
        scanner = AdvancedSecurityScanner()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def safe_function():\n    return "safe code"\n')
            temp_file = f.name
        
        try:
            vulnerabilities = scanner.scan_file(temp_file)
            
            # Should not find vulnerabilities in safe code
            assert len(vulnerabilities) == 0
        
        finally:
            os.unlink(temp_file)

    def test_get_security_score_no_vulnerabilities(self):
        """Test security score with no vulnerabilities."""
        scanner = AdvancedSecurityScanner()
        
        score = scanner.get_security_score()
        assert score == 100.0

    def test_generate_security_report(self):
        """Test generating security report."""
        scanner = AdvancedSecurityScanner()
        
        report = scanner.generate_security_report()
        
        assert report['total_vulnerabilities'] == 0
        assert report['security_score'] == 100.0
        assert len(report['vulnerabilities']) == 0