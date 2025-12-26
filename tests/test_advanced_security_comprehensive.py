"""Comprehensive tests for advanced_security.py module."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.ai_guard.advanced_security import (
    ThreatLevel,
    ComplianceStandard,
    SecurityIncidentType,
    Threat,
    Vulnerability,
    SecurityIncident,
    ThreatDetectionEngine,
    ComplianceManager,
    SecurityIncidentManager,
    AdvancedSecuritySystem,
    get_advanced_security_system,
    initialize_advanced_security,
)


class TestEnums:
    """Test enum classes."""

    def test_threat_level_values(self):
        """Test ThreatLevel enum values."""
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.CRITICAL.value == "critical"

    def test_compliance_standard_values(self):
        """Test ComplianceStandard enum values."""
        assert ComplianceStandard.SOC2.value == "soc2"
        assert ComplianceStandard.ISO27001.value == "iso27001"
        assert ComplianceStandard.PCI_DSS.value == "pci_dss"

    def test_security_incident_type_values(self):
        """Test SecurityIncidentType enum values."""
        assert SecurityIncidentType.MALWARE_DETECTED.value == "malware_detected"
        assert SecurityIncidentType.DATA_BREACH.value == "data_breach"


class TestThreatDetectionEngine:
    """Test ThreatDetectionEngine class."""

    def test_init(self):
        """Test threat detection engine initialization."""
        engine = ThreatDetectionEngine()
        assert engine.threats == []
        assert len(engine.threat_patterns) > 0

    def test_scan_content_no_threats(self):
        """Test scanning content with no threats."""
        engine = ThreatDetectionEngine()
        threats = engine.scan_content("def hello():\n    print('hello')")
        assert len(threats) == 0

    def test_scan_content_sql_injection(self):
        """Test scanning content for SQL injection."""
        engine = ThreatDetectionEngine()
        code = "query = 'SELECT * FROM users WHERE id = %s' % user_id"
        threats = engine.scan_content(code)
        assert len(threats) > 0

    def test_scan_content_hardcoded_secrets(self):
        """Test scanning content for hardcoded secrets."""
        engine = ThreatDetectionEngine()
        code = 'password = "secret123"'
        threats = engine.scan_content(code)
        assert len(threats) > 0

    def test_scan_content_command_injection(self):
        """Test scanning content for command injection."""
        engine = ThreatDetectionEngine()
        code = "import os\nos.system('rm -rf /')"
        threats = engine.scan_content(code)
        assert len(threats) > 0

    def test_get_threat_statistics_empty(self):
        """Test getting threat statistics with no threats."""
        engine = ThreatDetectionEngine()
        stats = engine.get_threat_statistics()
        assert stats["total_threats"] == 0

    def test_get_threat_statistics(self):
        """Test getting threat statistics."""
        engine = ThreatDetectionEngine()
        engine.scan_content('password = "secret"')
        stats = engine.get_threat_statistics()
        assert stats["total_threats"] > 0
        assert "threats_by_type" in stats
        assert "threats_by_severity" in stats


class TestComplianceManager:
    """Test ComplianceManager class."""

    def test_init(self):
        """Test compliance manager initialization."""
        manager = ComplianceManager()
        assert len(manager.compliance_frameworks) > 0

    def test_assess_compliance(self):
        """Test assessing compliance."""
        manager = ComplianceManager()
        result = manager.assess_compliance(ComplianceStandard.SOC2)
        assert "framework_name" in result or "compliance_percentage" in result
        assert isinstance(result, dict)


class TestSecurityIncidentManager:
    """Test SecurityIncidentManager class."""

    def test_init(self):
        """Test security incident manager initialization."""
        manager = SecurityIncidentManager()
        assert manager.incidents == []

    def test_create_incident(self):
        """Test creating a security incident."""
        manager = SecurityIncidentManager()
        incident = manager.create_incident(
            SecurityIncidentType.SUSPICIOUS_ACTIVITY,
            "Test Incident",
            "Test description",
            ThreatLevel.MEDIUM,
        )
        assert incident.title == "Test Incident"
        assert incident in manager.incidents
        assert len(manager.incidents) == 1


class TestAdvancedSecuritySystem:
    """Test AdvancedSecuritySystem class."""

    def test_init(self):
        """Test advanced security system initialization."""
        system = AdvancedSecuritySystem()
        assert system.threat_detector is not None
        assert system.compliance_manager is not None
        assert system.incident_manager is not None

    def test_perform_security_scan(self):
        """Test performing security scan."""
        system = AdvancedSecuritySystem()
        result = system.perform_security_scan('password = "secret"', "test.py")
        assert "threats_detected" in result
        assert "compliance_status" in result
        assert isinstance(result, dict)


class TestGlobalFunctions:
    """Test global functions."""

    def test_get_advanced_security_system(self):
        """Test getting advanced security system."""
        system1 = get_advanced_security_system()
        system2 = get_advanced_security_system()
        assert system1 is system2  # Singleton

    def test_initialize_advanced_security(self):
        """Test initializing advanced security."""
        result = initialize_advanced_security()
        assert result is True

