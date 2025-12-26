"""Integration module for the enhanced report system."""

import asyncio
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

from .report_optimized import (
    EnhancedReportGenerator,
    ReportConfig,
    ReportFormat,
    ReportType,
    ReportStatus,
    ReportData,
    ReportMetrics,
    ReportAnalytics,
    ReportScheduler,
    generate_enhanced_report,
    create_report_comparison,
)
from .cache import CacheManager, CacheConfig
from .config import Config


logger = logging.getLogger(__name__)


class ReportIntegrationManager:
    """Manages integration between report system and other AI-Guard components."""

    def __init__(self, config_manager: Optional[Config] = None):
        self.config_manager = config_manager or Config()
        self.report_generator = EnhancedReportGenerator()
        self.scheduler = ReportScheduler(self.report_generator)
        self.analytics = ReportAnalytics()
        self.cache_manager = CacheManager(
            CacheConfig(
                strategy="lru",
                max_size=1000,
                ttl=3600,
                enable_compression=True,
            )
        )
        self._active_integrations: Dict[str, Any] = {}

    def integrate_with_analyzer(
        self,
        analyzer_results: Dict[str, Any],
        report_config: Optional[ReportConfig] = None,
        auto_generate: bool = True,
    ) -> Dict[str, Any]:
        """Integrate analyzer results with report system."""
        try:
            # Prepare analysis results for report generation
            report_data = self._prepare_analyzer_results(analyzer_results)

            if auto_generate:
                # Generate report automatically
                config = report_config or ReportConfig()
                self.report_generator.config = config

                report = self.report_generator.generate_report(
                    analysis_results=report_data,
                    title=f"Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    description="Automated report from analyzer integration",
                )

                # Cache the report
                cache_key = f"analyzer_report_{report.report_id}"
                self.cache_manager.set(cache_key, report)

                return {
                    "success": True,
                    "report_id": report.report_id,
                    "report_data": report,
                    "integration_type": "analyzer",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            return {
                "success": True,
                "prepared_data": report_data,
                "integration_type": "analyzer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Analyzer integration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "integration_type": "analyzer",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def integrate_with_security_scanner(
        self,
        security_results: Dict[str, Any],
        report_config: Optional[ReportConfig] = None,
        auto_generate: bool = True,
    ) -> Dict[str, Any]:
        """Integrate security scanner results with report system."""
        try:
            # Prepare security results for report generation
            report_data = self._prepare_security_results(security_results)

            if auto_generate:
                config = report_config or ReportConfig(format=ReportFormat.HTML)
                self.report_generator.config = config

                report = self.report_generator.generate_report(
                    analysis_results=report_data,
                    title=f"Security Scan Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    description="Security vulnerability analysis report",
                )

                # Cache the report
                cache_key = f"security_report_{report.report_id}"
                self.cache_manager.set(cache_key, report)

                return {
                    "success": True,
                    "report_id": report.report_id,
                    "report_data": report,
                    "integration_type": "security_scanner",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            return {
                "success": True,
                "prepared_data": report_data,
                "integration_type": "security_scanner",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Security scanner integration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "integration_type": "security_scanner",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def integrate_with_performance_monitor(
        self,
        performance_data: Dict[str, Any],
        report_config: Optional[ReportConfig] = None,
        auto_generate: bool = True,
    ) -> Dict[str, Any]:
        """Integrate performance monitoring data with report system."""
        try:
            # Prepare performance data for report generation
            report_data = self._prepare_performance_data(performance_data)

            if auto_generate:
                config = report_config or ReportConfig(format=ReportFormat.JSON)
                self.report_generator.config = config

                report = self.report_generator.generate_report(
                    analysis_results=report_data,
                    title=f"Performance Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    description="System performance analysis report",
                )

                # Cache the report
                cache_key = f"performance_report_{report.report_id}"
                self.cache_manager.set(cache_key, report)

                return {
                    "success": True,
                    "report_id": report.report_id,
                    "report_data": report,
                    "integration_type": "performance_monitor",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            return {
                "success": True,
                "prepared_data": report_data,
                "integration_type": "performance_monitor",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Performance monitor integration failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "integration_type": "performance_monitor",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def create_comprehensive_report(
        self,
        analyzer_results: Dict[str, Any],
        security_results: Dict[str, Any],
        performance_data: Dict[str, Any],
        report_config: Optional[ReportConfig] = None,
    ) -> Dict[str, Any]:
        """Create a comprehensive report combining all system data."""
        try:
            # Combine all data sources
            combined_data = self._combine_data_sources(
                analyzer_results, security_results, performance_data
            )

            config = report_config or ReportConfig(
                format=ReportFormat.HTML,
                report_type=ReportType.DETAILED,
                include_metadata=True,
            )

            self.report_generator.config = config

            report = self.report_generator.generate_report(
                analysis_results=combined_data,
                title=f"Comprehensive AI-Guard Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description="Complete analysis report combining all system components",
            )

            # Cache the comprehensive report
            cache_key = f"comprehensive_report_{report.report_id}"
            self.cache_manager.set(cache_key, report)

            return {
                "success": True,
                "report_id": report.report_id,
                "report_data": report,
                "integration_type": "comprehensive",
                "data_sources": ["analyzer", "security_scanner", "performance_monitor"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Comprehensive report creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "integration_type": "comprehensive",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def setup_automated_reporting(
        self,
        schedule_configs: List[Dict[str, Any]],
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """Setup automated reporting with scheduled generation."""
        try:
            scheduled_reports = []

            for config in schedule_configs:
                schedule_id = f"auto_{int(time.time())}_{len(scheduled_reports)}"

                # Schedule the report
                self.scheduler.schedule_report(
                    schedule_id=schedule_id,
                    analysis_results=config.get("analysis_results", {}),
                    schedule_interval=config.get("interval", 3600),
                    output_path=config.get("output_path", "/tmp/automated_reports"),
                    formats=[
                        ReportFormat(fmt) for fmt in config.get("formats", ["json"])
                    ],
                )

                scheduled_reports.append(
                    {
                        "schedule_id": schedule_id,
                        "config": config,
                        "callback": callback,
                    }
                )

            # Store integration info
            integration_id = f"automated_reporting_{int(time.time())}"
            self._active_integrations[integration_id] = {
                "type": "automated_reporting",
                "scheduled_reports": scheduled_reports,
                "created_at": datetime.now(timezone.utc),
            }

            return {
                "success": True,
                "integration_id": integration_id,
                "scheduled_reports": len(scheduled_reports),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Automated reporting setup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def create_trend_analysis_report(
        self,
        historical_reports: List[ReportData],
        analysis_period: str = "7d",
    ) -> Dict[str, Any]:
        """Create a trend analysis report from historical data."""
        try:
            if len(historical_reports) < 2:
                return {
                    "success": False,
                    "error": "At least 2 historical reports required for trend analysis",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            # Create comparison data
            comparison_data = create_report_comparison(historical_reports, "trend")

            # Generate trend report
            config = ReportConfig(
                format=ReportFormat.HTML,
                report_type=ReportType.TREND,
                include_metadata=True,
            )

            self.report_generator.config = config

            trend_report = self.report_generator.generate_report(
                analysis_results={
                    "comparison_data": comparison_data,
                    "analysis_period": analysis_period,
                    "historical_reports": [
                        {
                            "report_id": r.report_id,
                            "timestamp": r.timestamp.isoformat(),
                            "issues_count": len(r.entries),
                            "generation_time": r.metrics.duration,
                        }
                        for r in historical_reports
                    ],
                },
                title=f"Trend Analysis Report - {analysis_period}",
                description="Analysis of trends across multiple report generations",
            )

            return {
                "success": True,
                "report_id": trend_report.report_id,
                "report_data": trend_report,
                "comparison_data": comparison_data,
                "analysis_period": analysis_period,
                "historical_reports_count": len(historical_reports),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Trend analysis report creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def export_integration_data(
        self,
        integration_id: str,
        export_formats: List[ReportFormat],
        output_directory: str,
    ) -> Dict[str, Any]:
        """Export data from a specific integration."""
        try:
            if integration_id not in self._active_integrations:
                return {
                    "success": False,
                    "error": f"Integration {integration_id} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            integration = self._active_integrations[integration_id]
            export_results = {}

            if integration["type"] == "automated_reporting":
                # Export scheduled report configurations
                for scheduled_report in integration["scheduled_reports"]:
                    schedule_id = scheduled_report["schedule_id"]
                    config = scheduled_report["config"]

                    export_data = {
                        "schedule_id": schedule_id,
                        "config": config,
                        "created_at": integration["created_at"].isoformat(),
                    }

                    for fmt in export_formats:
                        if fmt == ReportFormat.JSON:
                            file_path = os.path.join(
                                output_directory, f"{schedule_id}.json"
                            )
                            with open(file_path, "w") as f:
                                json.dump(export_data, f, indent=2)
                            export_results[schedule_id] = {
                                "format": fmt.value,
                                "file_path": file_path,
                            }

            return {
                "success": True,
                "integration_id": integration_id,
                "export_results": export_results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Integration data export failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all active integrations."""
        try:
            status = {
                "total_integrations": len(self._active_integrations),
                "integration_types": {},
                "cache_stats": self.cache_manager.get_stats(),
                "analytics": self.analytics.get_performance_stats(),
                "scheduler_stats": {
                    "scheduled_reports": len(self.scheduler.scheduled_reports),
                    "active_schedules": len(
                        [
                            s
                            for s in self.scheduler.scheduled_reports.values()
                            if s.get("active", False)
                        ]
                    ),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Count integration types
            for integration in self._active_integrations.values():
                integration_type = integration["type"]
                status["integration_types"][integration_type] = (
                    status["integration_types"].get(integration_type, 0) + 1
                )

            return status

        except Exception as e:
            logger.error(f"Integration status retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def cleanup_integration(self, integration_id: str) -> Dict[str, Any]:
        """Clean up a specific integration."""
        try:
            if integration_id not in self._active_integrations:
                return {
                    "success": False,
                    "error": f"Integration {integration_id} not found",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            integration = self._active_integrations[integration_id]

            # Clean up based on integration type
            if integration["type"] == "automated_reporting":
                for scheduled_report in integration["scheduled_reports"]:
                    schedule_id = scheduled_report["schedule_id"]
                    self.scheduler.cancel_schedule(schedule_id)

            # Remove from active integrations
            del self._active_integrations[integration_id]

            return {
                "success": True,
                "integration_id": integration_id,
                "cleanup_type": integration["type"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Integration cleanup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _prepare_analyzer_results(
        self, analyzer_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare analyzer results for report generation."""
        issues = []

        # Extract issues from analyzer results
        if "issues" in analyzer_results:
            issues.extend(analyzer_results["issues"])

        if "findings" in analyzer_results:
            issues.extend(analyzer_results["findings"])

        if "violations" in analyzer_results:
            issues.extend(analyzer_results["violations"])

        # Standardize issue format
        standardized_issues = []
        for issue in issues:
            standardized_issue = {
                "type": issue.get("type", "unknown"),
                "severity": issue.get("severity", issue.get("level", "warning")),
                "message": issue.get("message", issue.get("description", "")),
                "file": issue.get("file", issue.get("path", "unknown")),
                "line": issue.get("line", issue.get("line_number")),
                "column": issue.get("column", issue.get("column_number")),
                "rule_id": issue.get("rule_id", issue.get("rule")),
                "metadata": issue.get("metadata", {}),
            }
            standardized_issues.append(standardized_issue)

        return {
            "issues": standardized_issues,
            "source": "analyzer",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _prepare_security_results(
        self, security_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare security scanner results for report generation."""
        issues = []

        # Extract security findings
        if "vulnerabilities" in security_results:
            for vuln in security_results["vulnerabilities"]:
                issues.append(
                    {
                        "type": "vulnerability",
                        "severity": vuln.get("severity", "medium"),
                        "message": vuln.get("description", vuln.get("message", "")),
                        "file": vuln.get("file", vuln.get("path", "unknown")),
                        "line": vuln.get("line"),
                        "column": vuln.get("column"),
                        "rule_id": vuln.get("cve_id", vuln.get("rule_id", "")),
                        "metadata": {
                            "cve_id": vuln.get("cve_id"),
                            "cvss_score": vuln.get("cvss_score"),
                            "package": vuln.get("package"),
                            "version": vuln.get("version"),
                            **vuln.get("metadata", {}),
                        },
                    }
                )

        if "security_issues" in security_results:
            issues.extend(security_results["security_issues"])

        return {
            "issues": issues,
            "source": "security_scanner",
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "security_summary": {
                "total_vulnerabilities": len(
                    [i for i in issues if i["type"] == "vulnerability"]
                ),
                "high_severity": len([i for i in issues if i["severity"] == "high"]),
                "medium_severity": len(
                    [i for i in issues if i["severity"] == "medium"]
                ),
                "low_severity": len([i for i in issues if i["severity"] == "low"]),
            },
        }

    def _prepare_performance_data(
        self, performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare performance monitoring data for report generation."""
        issues = []

        # Extract performance issues
        if "performance_issues" in performance_data:
            for perf_issue in performance_data["performance_issues"]:
                issues.append(
                    {
                        "type": "performance",
                        "severity": perf_issue.get("severity", "warning"),
                        "message": perf_issue.get(
                            "description", perf_issue.get("message", "")
                        ),
                        "file": perf_issue.get(
                            "file", perf_issue.get("path", "unknown")
                        ),
                        "line": perf_issue.get("line"),
                        "column": perf_issue.get("column"),
                        "rule_id": perf_issue.get("rule_id", "PERF"),
                        "metadata": {
                            "execution_time": perf_issue.get("execution_time"),
                            "memory_usage": perf_issue.get("memory_usage"),
                            "cpu_usage": perf_issue.get("cpu_usage"),
                            "threshold": perf_issue.get("threshold"),
                            **perf_issue.get("metadata", {}),
                        },
                    }
                )

        return {
            "issues": issues,
            "source": "performance_monitor",
            "monitoring_timestamp": datetime.now(timezone.utc).isoformat(),
            "performance_summary": {
                "total_issues": len(issues),
                "avg_execution_time": performance_data.get("avg_execution_time"),
                "peak_memory_usage": performance_data.get("peak_memory_usage"),
                "cpu_utilization": performance_data.get("cpu_utilization"),
            },
        }

    def _combine_data_sources(
        self,
        analyzer_results: Dict[str, Any],
        security_results: Dict[str, Any],
        performance_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Combine data from all sources into a comprehensive dataset."""
        # Prepare data from each source
        analyzer_data = self._prepare_analyzer_results(analyzer_results)
        security_data = self._prepare_security_results(security_results)
        performance_prepared = self._prepare_performance_data(performance_data)

        # Combine all issues
        all_issues = []
        all_issues.extend(analyzer_data.get("issues", []))
        all_issues.extend(security_data.get("issues", []))
        all_issues.extend(performance_prepared.get("issues", []))

        # Create comprehensive summary
        comprehensive_summary = {
            "total_issues": len(all_issues),
            "by_source": {
                "analyzer": len(analyzer_data.get("issues", [])),
                "security_scanner": len(security_data.get("issues", [])),
                "performance_monitor": len(performance_prepared.get("issues", [])),
            },
            "by_severity": {},
            "by_type": {},
        }

        # Count by severity and type
        for issue in all_issues:
            severity = issue.get("severity", "unknown")
            issue_type = issue.get("type", "unknown")

            comprehensive_summary["by_severity"][severity] = (
                comprehensive_summary["by_severity"].get(severity, 0) + 1
            )
            comprehensive_summary["by_type"][issue_type] = (
                comprehensive_summary["by_type"].get(issue_type, 0) + 1
            )

        return {
            "issues": all_issues,
            "source": "comprehensive",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "comprehensive_summary": comprehensive_summary,
            "source_data": {
                "analyzer": analyzer_data,
                "security_scanner": security_data,
                "performance_monitor": performance_prepared,
            },
        }


class ReportDashboard:
    """Dashboard for monitoring and managing report integrations."""

    def __init__(self, integration_manager: ReportIntegrationManager):
        self.integration_manager = integration_manager

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        try:
            integration_status = self.integration_manager.get_integration_status()
            analytics = self.integration_manager.analytics.get_performance_stats()
            trend_analysis = self.integration_manager.analytics.get_trend_analysis()

            return {
                "dashboard": {
                    "integration_status": integration_status,
                    "analytics": analytics,
                    "trend_analysis": trend_analysis,
                    "system_health": self._assess_system_health(),
                    "recent_activity": self._get_recent_activity(),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Dashboard data retrieval failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health."""
        cache_stats = self.integration_manager.cache_manager.get_stats()

        # Calculate health metrics
        cache_hit_rate = cache_stats.get("hit_rate", 0)
        error_rate = self.integration_manager.analytics.error_counts
        total_errors = sum(error_rate.values()) if error_rate else 0

        health_score = 100
        if cache_hit_rate < 0.7:
            health_score -= 20
        if total_errors > 10:
            health_score -= 30

        return {
            "overall_score": max(0, health_score),
            "cache_health": (
                "good"
                if cache_hit_rate > 0.8
                else "warning" if cache_hit_rate > 0.6 else "poor"
            ),
            "error_health": (
                "good"
                if total_errors < 5
                else "warning" if total_errors < 15 else "poor"
            ),
            "recommendations": self._generate_health_recommendations(
                cache_hit_rate, total_errors
            ),
        }

    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity summary."""
        # This would typically query a database or log system
        # For now, return mock data
        return [
            {
                "type": "report_generated",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "description": "Security scan report generated",
            },
            {
                "type": "integration_created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "description": "Automated reporting integration setup",
            },
        ]

    def _generate_health_recommendations(
        self, cache_hit_rate: float, total_errors: int
    ) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []

        if cache_hit_rate < 0.7:
            recommendations.append(
                "Consider increasing cache size or TTL to improve hit rate"
            )

        if total_errors > 10:
            recommendations.append("Review error logs and fix underlying issues")

        if not recommendations:
            recommendations.append("System is performing well")

        return recommendations


# Convenience functions
def create_integration_manager(
    config_manager: Optional[Config] = None,
) -> ReportIntegrationManager:
    """Create a new integration manager instance."""
    return ReportIntegrationManager(config_manager)


def create_dashboard(integration_manager: ReportIntegrationManager) -> ReportDashboard:
    """Create a new dashboard instance."""
    return ReportDashboard(integration_manager)


def quick_report_from_analyzer(
    analyzer_results: Dict[str, Any],
    output_path: Optional[str] = None,
    format_type: str = "html",
) -> Dict[str, Any]:
    """Quickly generate a report from analyzer results."""
    integration_manager = create_integration_manager()

    result = integration_manager.integrate_with_analyzer(
        analyzer_results=analyzer_results,
        report_config=ReportConfig(format=ReportFormat(format_type)),
        auto_generate=True,
    )

    if result["success"] and output_path:
        export_results = integration_manager.report_generator.export_report(
            result["report_data"], output_path, [ReportFormat(format_type)]
        )
        result["export_results"] = export_results

    return result


def quick_comprehensive_report(
    analyzer_results: Dict[str, Any],
    security_results: Dict[str, Any],
    performance_data: Dict[str, Any],
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Quickly generate a comprehensive report from all data sources."""
    integration_manager = create_integration_manager()

    result = integration_manager.create_comprehensive_report(
        analyzer_results=analyzer_results,
        security_results=security_results,
        performance_data=performance_data,
    )

    if result["success"] and output_path:
        export_results = integration_manager.report_generator.export_report(
            result["report_data"], output_path, [ReportFormat.HTML, ReportFormat.JSON]
        )
        result["export_results"] = export_results

    return result
