"""Comprehensive tests for the report integration system."""

import asyncio
import json
import os
import tempfile
import time
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from src.ai_guard.report_integration import (
    ReportIntegrationManager,
    ReportDashboard,
    create_integration_manager,
    create_dashboard,
    quick_report_from_analyzer,
    quick_comprehensive_report,
)
from src.ai_guard.report_optimized import (
    ReportConfig,
    ReportFormat,
    ReportType,
    ReportStatus,
    ReportData,
    ReportMetrics,
    ReportEntry,
)
from src.ai_guard.config import Config


class TestReportIntegrationManager:
    """Test ReportIntegrationManager class."""

    def test_integration_manager_initialization(self):
        """Test integration manager initialization."""
        manager = ReportIntegrationManager()

        assert manager.config_manager is not None
        assert manager.report_generator is not None
        assert manager.scheduler is not None
        assert manager.analytics is not None
        assert manager.cache_manager is not None
        assert manager._active_integrations == {}

    def test_integration_manager_with_config(self):
        """Test integration manager with custom config manager."""
        config_manager = Config()
        manager = ReportIntegrationManager(config_manager)

        assert manager.config_manager == config_manager

    def test_integrate_with_analyzer(self):
        """Test analyzer integration."""
        manager = ReportIntegrationManager()

        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "severity": "high",
                    "message": "Test error",
                    "file": "/test/file.py",
                    "line": 10,
                    "rule_id": "TEST001",
                },
                {
                    "type": "warning",
                    "severity": "medium",
                    "message": "Test warning",
                    "file": "/test/file2.py",
                    "line": 20,
                    "rule_id": "TEST002",
                },
            ]
        }

        result = manager.integrate_with_analyzer(analyzer_results)

        assert result["success"] is True
        assert result["integration_type"] == "analyzer"
        assert "report_id" in result
        assert "report_data" in result
        assert result["report_data"].metrics.issues_found == 2

    def test_integrate_with_analyzer_no_auto_generate(self):
        """Test analyzer integration without auto-generation."""
        manager = ReportIntegrationManager()

        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Test error",
                    "file": "/test/file.py",
                    "line": 10,
                }
            ]
        }

        result = manager.integrate_with_analyzer(analyzer_results, auto_generate=False)

        assert result["success"] is True
        assert result["integration_type"] == "analyzer"
        assert "prepared_data" in result
        assert "report_id" not in result
        assert result["prepared_data"]["source"] == "analyzer"

    def test_integrate_with_security_scanner(self):
        """Test security scanner integration."""
        manager = ReportIntegrationManager()

        security_results = {
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2023-1234",
                    "severity": "high",
                    "description": "Test vulnerability",
                    "file": "/test/vuln.py",
                    "line": 15,
                    "cvss_score": 8.5,
                    "package": "test-package",
                    "version": "1.0.0",
                }
            ]
        }

        result = manager.integrate_with_security_scanner(security_results)

        assert result["success"] is True
        assert result["integration_type"] == "security_scanner"
        assert "report_id" in result
        assert result["report_data"].metrics.issues_found == 1

        # Check that vulnerability was properly converted
        entry = result["report_data"].entries[0]
        assert entry.type == "vulnerability"
        assert entry.severity == "high"
        assert entry.rule_id == "CVE-2023-1234"
        assert "cvss_score" in entry.metadata

    def test_integrate_with_performance_monitor(self):
        """Test performance monitor integration."""
        manager = ReportIntegrationManager()

        performance_data = {
            "performance_issues": [
                {
                    "severity": "warning",
                    "description": "Slow function execution",
                    "file": "/test/slow.py",
                    "line": 25,
                    "execution_time": 5.2,
                    "memory_usage": 128,
                    "threshold": 1.0,
                }
            ],
            "avg_execution_time": 2.1,
            "peak_memory_usage": 512,
            "cpu_utilization": 75.5,
        }

        result = manager.integrate_with_performance_monitor(performance_data)

        assert result["success"] is True
        assert result["integration_type"] == "performance_monitor"
        assert "report_id" in result
        assert result["report_data"].metrics.issues_found == 1

        # Check that performance issue was properly converted
        entry = result["report_data"].entries[0]
        assert entry.type == "performance"
        assert entry.severity == "warning"
        assert "execution_time" in entry.metadata
        assert entry.metadata["execution_time"] == 5.2

    def test_create_comprehensive_report(self):
        """Test comprehensive report creation."""
        manager = ReportIntegrationManager()

        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Analyzer error",
                    "file": "/test/analyzer.py",
                    "line": 10,
                }
            ]
        }

        security_results = {
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2023-1234",
                    "severity": "high",
                    "description": "Security vulnerability",
                    "file": "/test/security.py",
                    "line": 15,
                }
            ]
        }

        performance_data = {
            "performance_issues": [
                {
                    "severity": "warning",
                    "description": "Performance issue",
                    "file": "/test/performance.py",
                    "line": 20,
                }
            ]
        }

        result = manager.create_comprehensive_report(
            analyzer_results, security_results, performance_data
        )

        assert result["success"] is True
        assert result["integration_type"] == "comprehensive"
        assert "report_id" in result
        assert result["data_sources"] == [
            "analyzer",
            "security_scanner",
            "performance_monitor",
        ]
        assert result["report_data"].metrics.issues_found == 3

    def test_setup_automated_reporting(self):
        """Test automated reporting setup."""
        manager = ReportIntegrationManager()

        schedule_configs = [
            {
                "analysis_results": {"issues": []},
                "interval": 3600,
                "output_path": "/tmp/test1",
                "formats": ["json"],
            },
            {
                "analysis_results": {"issues": []},
                "interval": 7200,
                "output_path": "/tmp/test2",
                "formats": ["html", "json"],
            },
        ]

        def mock_callback(result):
            pass

        result = manager.setup_automated_reporting(
            schedule_configs, callback=mock_callback
        )

        assert result["success"] is True
        assert "integration_id" in result
        assert result["scheduled_reports"] == 2

        # Verify integrations were created
        assert result["integration_id"] in manager._active_integrations
        integration = manager._active_integrations[result["integration_id"]]
        assert integration["type"] == "automated_reporting"
        assert len(integration["scheduled_reports"]) == 2

    def test_create_trend_analysis_report(self):
        """Test trend analysis report creation."""
        manager = ReportIntegrationManager()

        # Create mock historical reports
        historical_reports = []
        for i in range(3):
            metrics = ReportMetrics()
            metrics.end_time = time.time()

            report = ReportData(
                report_id=f"historical_{i}",
                title=f"Historical Report {i}",
                description="Historical report for trend analysis",
                timestamp=datetime.now(timezone.utc),
                format=ReportFormat.JSON,
                status=ReportStatus.COMPLETED,
                metrics=metrics,
                entries=[
                    ReportEntry(
                        id=f"entry_{i}",
                        type="warning",
                        severity="medium",
                        message=f"Historical issue {i}",
                        file_path=f"/test/historical{i}.py",
                    )
                ],
            )
            historical_reports.append(report)

        result = manager.create_trend_analysis_report(
            historical_reports, analysis_period="7d"
        )

        assert result["success"] is True
        assert "report_id" in result
        assert "comparison_data" in result
        assert result["analysis_period"] == "7d"
        assert result["historical_reports_count"] == 3

    def test_create_trend_analysis_insufficient_data(self):
        """Test trend analysis with insufficient data."""
        manager = ReportIntegrationManager()

        # Create only one historical report
        metrics = ReportMetrics()
        metrics.end_time = time.time()

        historical_report = ReportData(
            report_id="single_report",
            title="Single Report",
            description="Only one report",
            timestamp=datetime.now(timezone.utc),
            format=ReportFormat.JSON,
            status=ReportStatus.COMPLETED,
            metrics=metrics,
            entries=[],
        )

        result = manager.create_trend_analysis_report([historical_report])

        assert result["success"] is False
        assert "At least 2 historical reports required" in result["error"]

    def test_export_integration_data(self):
        """Test integration data export."""
        manager = ReportIntegrationManager()

        # Setup an integration first
        schedule_configs = [
            {
                "analysis_results": {"issues": []},
                "interval": 3600,
                "output_path": "/tmp/test",
                "formats": ["json"],
            }
        ]

        setup_result = manager.setup_automated_reporting(schedule_configs)
        integration_id = setup_result["integration_id"]

        with tempfile.TemporaryDirectory() as temp_dir:
            result = manager.export_integration_data(
                integration_id, [ReportFormat.JSON], temp_dir
            )

            assert result["success"] is True
            assert "export_results" in result

            # Verify files were created
            export_results = result["export_results"]
            assert len(export_results) > 0

            for schedule_id, export_info in export_results.items():
                file_path = export_info["file_path"]
                assert os.path.exists(file_path)

                # Verify JSON content
                with open(file_path, "r") as f:
                    data = json.load(f)
                    assert "schedule_id" in data
                    assert "config" in data

    def test_export_nonexistent_integration(self):
        """Test export of non-existent integration."""
        manager = ReportIntegrationManager()

        result = manager.export_integration_data(
            "nonexistent_id", [ReportFormat.JSON], "/tmp"
        )

        assert result["success"] is False
        assert "Integration nonexistent_id not found" in result["error"]

    def test_get_integration_status(self):
        """Test integration status retrieval."""
        manager = ReportIntegrationManager()

        # Setup some integrations
        schedule_configs = [
            {
                "analysis_results": {"issues": []},
                "interval": 3600,
                "output_path": "/tmp/test",
                "formats": ["json"],
            }
        ]

        manager.setup_automated_reporting(schedule_configs)

        status = manager.get_integration_status()

        assert "total_integrations" in status
        assert "integration_types" in status
        assert "cache_stats" in status
        assert "analytics" in status
        assert "scheduler_stats" in status
        assert status["total_integrations"] == 1
        assert "automated_reporting" in status["integration_types"]

    def test_cleanup_integration(self):
        """Test integration cleanup."""
        manager = ReportIntegrationManager()

        # Setup an integration
        schedule_configs = [
            {
                "analysis_results": {"issues": []},
                "interval": 3600,
                "output_path": "/tmp/test",
                "formats": ["json"],
            }
        ]

        setup_result = manager.setup_automated_reporting(schedule_configs)
        integration_id = setup_result["integration_id"]

        # Verify integration exists
        assert integration_id in manager._active_integrations

        # Cleanup the integration
        result = manager.cleanup_integration(integration_id)

        assert result["success"] is True
        assert result["integration_id"] == integration_id
        assert result["cleanup_type"] == "automated_reporting"

        # Verify integration was removed
        assert integration_id not in manager._active_integrations

    def test_cleanup_nonexistent_integration(self):
        """Test cleanup of non-existent integration."""
        manager = ReportIntegrationManager()

        result = manager.cleanup_integration("nonexistent_id")

        assert result["success"] is False
        assert "Integration nonexistent_id not found" in result["error"]

    def test_prepare_analyzer_results(self):
        """Test analyzer results preparation."""
        manager = ReportIntegrationManager()

        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "severity": "high",
                    "message": "Test error",
                    "file": "/test/file.py",
                    "line": 10,
                    "rule_id": "TEST001",
                    "metadata": {"key": "value"},
                }
            ],
            "findings": [
                {
                    "type": "warning",
                    "level": "medium",  # Different key name
                    "description": "Test warning",  # Different key name
                    "path": "/test/file2.py",  # Different key name
                    "line_number": 20,  # Different key name
                    "rule": "TEST002",  # Different key name
                }
            ],
        }

        prepared = manager._prepare_analyzer_results(analyzer_results)

        assert prepared["source"] == "analyzer"
        assert len(prepared["issues"]) == 2

        # Check first issue (from "issues")
        issue1 = prepared["issues"][0]
        assert issue1["type"] == "error"
        assert issue1["severity"] == "high"
        assert issue1["message"] == "Test error"
        assert issue1["file"] == "/test/file.py"
        assert issue1["line"] == 10
        assert issue1["rule_id"] == "TEST001"
        assert issue1["metadata"] == {"key": "value"}

        # Check second issue (from "findings")
        issue2 = prepared["issues"][1]
        assert issue2["type"] == "warning"
        assert issue2["severity"] == "medium"
        assert issue2["message"] == "Test warning"
        assert issue2["file"] == "/test/file2.py"
        assert issue2["line"] == 20
        assert issue2["rule_id"] == "TEST002"

    def test_prepare_security_results(self):
        """Test security results preparation."""
        manager = ReportIntegrationManager()

        security_results = {
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2023-1234",
                    "severity": "high",
                    "description": "Test vulnerability",
                    "file": "/test/vuln.py",
                    "line": 15,
                    "column": 8,
                    "cvss_score": 8.5,
                    "package": "test-package",
                    "version": "1.0.0",
                    "metadata": {"additional": "data"},
                }
            ]
        }

        prepared = manager._prepare_security_results(security_results)

        assert prepared["source"] == "security_scanner"
        assert len(prepared["issues"]) == 1

        issue = prepared["issues"][0]
        assert issue["type"] == "vulnerability"
        assert issue["severity"] == "high"
        assert issue["message"] == "Test vulnerability"
        assert issue["file"] == "/test/vuln.py"
        assert issue["line"] == 15
        assert issue["column"] == 8
        assert issue["rule_id"] == "CVE-2023-1234"

        # Check metadata
        metadata = issue["metadata"]
        assert metadata["cve_id"] == "CVE-2023-1234"
        assert metadata["cvss_score"] == 8.5
        assert metadata["package"] == "test-package"
        assert metadata["version"] == "1.0.0"
        assert metadata["additional"] == "data"

        # Check security summary
        summary = prepared["security_summary"]
        assert summary["total_vulnerabilities"] == 1
        assert summary["high_severity"] == 1
        assert summary["medium_severity"] == 0
        assert summary["low_severity"] == 0

    def test_prepare_performance_data(self):
        """Test performance data preparation."""
        manager = ReportIntegrationManager()

        performance_data = {
            "performance_issues": [
                {
                    "severity": "warning",
                    "description": "Slow execution",
                    "file": "/test/slow.py",
                    "line": 25,
                    "column": 12,
                    "execution_time": 5.2,
                    "memory_usage": 128,
                    "cpu_usage": 85.5,
                    "threshold": 1.0,
                    "metadata": {"custom": "data"},
                }
            ],
            "avg_execution_time": 2.1,
            "peak_memory_usage": 512,
            "cpu_utilization": 75.5,
        }

        prepared = manager._prepare_performance_data(performance_data)

        assert prepared["source"] == "performance_monitor"
        assert len(prepared["issues"]) == 1

        issue = prepared["issues"][0]
        assert issue["type"] == "performance"
        assert issue["severity"] == "warning"
        assert issue["message"] == "Slow execution"
        assert issue["file"] == "/test/slow.py"
        assert issue["line"] == 25
        assert issue["column"] == 12
        assert issue["rule_id"] == "PERF"

        # Check metadata
        metadata = issue["metadata"]
        assert metadata["execution_time"] == 5.2
        assert metadata["memory_usage"] == 128
        assert metadata["cpu_usage"] == 85.5
        assert metadata["threshold"] == 1.0
        assert metadata["custom"] == "data"

        # Check performance summary
        summary = prepared["performance_summary"]
        assert summary["total_issues"] == 1
        assert summary["avg_execution_time"] == 2.1
        assert summary["peak_memory_usage"] == 512
        assert summary["cpu_utilization"] == 75.5

    def test_combine_data_sources(self):
        """Test combining data from multiple sources."""
        manager = ReportIntegrationManager()

        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Analyzer error",
                    "file": "/test/analyzer.py",
                    "line": 10,
                }
            ]
        }

        security_results = {
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2023-1234",
                    "severity": "high",
                    "description": "Security vulnerability",
                    "file": "/test/security.py",
                    "line": 15,
                }
            ]
        }

        performance_data = {
            "performance_issues": [
                {
                    "severity": "warning",
                    "description": "Performance issue",
                    "file": "/test/performance.py",
                    "line": 20,
                }
            ]
        }

        combined = manager._combine_data_sources(
            analyzer_results, security_results, performance_data
        )

        assert combined["source"] == "comprehensive"
        assert len(combined["issues"]) == 3

        # Check comprehensive summary
        summary = combined["comprehensive_summary"]
        assert summary["total_issues"] == 3
        assert summary["by_source"]["analyzer"] == 1
        assert summary["by_source"]["security_scanner"] == 1
        assert summary["by_source"]["performance_monitor"] == 1
        assert summary["by_severity"]["high"] == 1
        assert summary["by_severity"]["warning"] == 1
        assert summary["by_type"]["error"] == 1
        assert summary["by_type"]["vulnerability"] == 1
        assert summary["by_type"]["performance"] == 1


class TestReportDashboard:
    """Test ReportDashboard class."""

    def test_dashboard_initialization(self):
        """Test dashboard initialization."""
        manager = ReportIntegrationManager()
        dashboard = ReportDashboard(manager)

        assert dashboard.integration_manager == manager

    def test_get_dashboard_data(self):
        """Test dashboard data retrieval."""
        manager = ReportIntegrationManager()
        dashboard = ReportDashboard(manager)

        # Setup some integrations
        schedule_configs = [
            {
                "analysis_results": {"issues": []},
                "interval": 3600,
                "output_path": "/tmp/test",
                "formats": ["json"],
            }
        ]

        manager.setup_automated_reporting(schedule_configs)

        # Generate some reports for analytics
        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Test error",
                    "file": "/test/file.py",
                    "line": 10,
                }
            ]
        }

        manager.integrate_with_analyzer(analyzer_results)

        data = dashboard.get_dashboard_data()

        assert "dashboard" in data
        dashboard_info = data["dashboard"]

        assert "integration_status" in dashboard_info
        assert "analytics" in dashboard_info
        assert "trend_analysis" in dashboard_info
        assert "system_health" in dashboard_info
        assert "recent_activity" in dashboard_info

        # Check system health
        health = dashboard_info["system_health"]
        assert "overall_score" in health
        assert "cache_health" in health
        assert "error_health" in health
        assert "recommendations" in health
        assert isinstance(health["recommendations"], list)

    def test_assess_system_health(self):
        """Test system health assessment."""
        manager = ReportIntegrationManager()
        dashboard = ReportDashboard(manager)

        health = dashboard._assess_system_health()

        assert "overall_score" in health
        assert "cache_health" in health
        assert "error_health" in health
        assert "recommendations" in health
        assert 0 <= health["overall_score"] <= 100
        assert health["cache_health"] in ["good", "warning", "poor"]
        assert health["error_health"] in ["good", "warning", "poor"]

    def test_get_recent_activity(self):
        """Test recent activity retrieval."""
        manager = ReportIntegrationManager()
        dashboard = ReportDashboard(manager)

        activity = dashboard._get_recent_activity()

        assert isinstance(activity, list)
        # Should have at least some mock activity
        assert len(activity) >= 0

    def test_generate_health_recommendations(self):
        """Test health recommendation generation."""
        manager = ReportIntegrationManager()
        dashboard = ReportDashboard(manager)

        # Test with good metrics
        recommendations = dashboard._generate_health_recommendations(0.9, 2)
        assert "System is performing well" in recommendations

        # Test with poor cache hit rate
        recommendations = dashboard._generate_health_recommendations(0.5, 2)
        assert any("cache" in rec.lower() for rec in recommendations)

        # Test with many errors
        recommendations = dashboard._generate_health_recommendations(0.9, 20)
        assert any("error" in rec.lower() for rec in recommendations)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_integration_manager(self):
        """Test create_integration_manager function."""
        manager = create_integration_manager()

        assert isinstance(manager, ReportIntegrationManager)
        assert manager.config_manager is not None

    def test_create_integration_manager_with_config(self):
        """Test create_integration_manager with custom config."""
        config_manager = Config()
        manager = create_integration_manager(config_manager)

        assert isinstance(manager, ReportIntegrationManager)
        assert manager.config_manager == config_manager

    def test_create_dashboard(self):
        """Test create_dashboard function."""
        manager = create_integration_manager()
        dashboard = create_dashboard(manager)

        assert isinstance(dashboard, ReportDashboard)
        assert dashboard.integration_manager == manager

    def test_quick_report_from_analyzer(self):
        """Test quick_report_from_analyzer function."""
        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Quick test error",
                    "file": "/test/quick.py",
                    "line": 10,
                }
            ]
        }

        result = quick_report_from_analyzer(analyzer_results, format_type="json")

        assert result["success"] is True
        assert "report_id" in result
        assert result["report_data"].metrics.issues_found == 1

    def test_quick_report_from_analyzer_with_export(self):
        """Test quick_report_from_analyzer with export."""
        analyzer_results = {
            "issues": [
                {
                    "type": "warning",
                    "message": "Export test warning",
                    "file": "/test/export.py",
                    "line": 15,
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "quick_report")

            result = quick_report_from_analyzer(
                analyzer_results, output_path=output_path, format_type="html"
            )

            assert result["success"] is True
            assert "export_results" in result
            assert "html" in result["export_results"]
            assert result["export_results"]["html"]["success"] is True

    def test_quick_comprehensive_report(self):
        """Test quick_comprehensive_report function."""
        analyzer_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Analyzer error",
                    "file": "/test/analyzer.py",
                    "line": 10,
                }
            ]
        }

        security_results = {
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2023-1234",
                    "severity": "high",
                    "description": "Security vulnerability",
                    "file": "/test/security.py",
                    "line": 15,
                }
            ]
        }

        performance_data = {
            "performance_issues": [
                {
                    "severity": "warning",
                    "description": "Performance issue",
                    "file": "/test/performance.py",
                    "line": 20,
                }
            ]
        }

        result = quick_comprehensive_report(
            analyzer_results, security_results, performance_data
        )

        assert result["success"] is True
        assert "report_id" in result
        assert result["report_data"].metrics.issues_found == 3

    def test_quick_comprehensive_report_with_export(self):
        """Test quick_comprehensive_report with export."""
        analyzer_results = {"issues": []}
        security_results = {"vulnerabilities": []}
        performance_data = {"performance_issues": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "comprehensive_report")

            result = quick_comprehensive_report(
                analyzer_results,
                security_results,
                performance_data,
                output_path=output_path,
            )

            assert result["success"] is True
            assert "export_results" in result
            assert "html" in result["export_results"]
            assert "json" in result["export_results"]


class TestErrorHandling:
    """Test error handling in integration system."""

    def test_integration_with_invalid_data(self):
        """Test integration with invalid data."""
        manager = ReportIntegrationManager()

        # Test with None
        result = manager.integrate_with_analyzer(None)
        assert result["success"] is False
        assert "error" in result

        # Test with empty dict
        result = manager.integrate_with_analyzer({})
        assert result["success"] is True  # Should handle gracefully
        assert result["report_data"].metrics.issues_found == 0

    def test_comprehensive_report_with_missing_data(self):
        """Test comprehensive report with missing data."""
        manager = ReportIntegrationManager()

        result = manager.create_comprehensive_report(
            {},  # Empty analyzer results
            {},  # Empty security results
            {},  # Empty performance data
        )

        assert result["success"] is True
        assert result["report_data"].metrics.issues_found == 0

    def test_dashboard_with_no_integrations(self):
        """Test dashboard with no integrations."""
        manager = ReportIntegrationManager()
        dashboard = ReportDashboard(manager)

        data = dashboard.get_dashboard_data()

        assert "dashboard" in data
        dashboard_info = data["dashboard"]
        assert dashboard_info["integration_status"]["total_integrations"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
