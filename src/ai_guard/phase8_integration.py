"""Phase 8 Integration System for AI-Guard.

This module provides unified orchestration of all Phase 8 components:
- Machine Learning Integration
- Real-time Monitoring and Alerting
- Enterprise Features (Multi-tenant, RBAC, Compliance)
- Advanced Analytics and Business Intelligence
- Cloud and DevOps Integration
- Advanced Security Features and Compliance Automation
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """System status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class IntegrationComponent:
    """Integration component information."""

    name: str
    status: SystemStatus
    last_check: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """System health information."""

    overall_status: SystemStatus
    components: List[IntegrationComponent] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    uptime_seconds: float = 0.0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0


@dataclass
class IntegrationReport:
    """Integration system report."""

    report_type: str
    generated_at: datetime = field(default_factory=datetime.now)
    system_health: Optional[SystemHealth] = None
    component_reports: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class Phase8IntegrationSystem:
    """Phase 8 Integration System orchestrating all advanced features."""

    def __init__(self):
        """Initialize the Phase 8 integration system."""
        self._lock = threading.RLock()
        self._start_time = time.time()
        self._components: Dict[str, IntegrationComponent] = {}
        self._initialized = False
        self._shutdown = False

        # Component managers
        self.ml_manager = None
        self.monitoring_system = None
        self.enterprise_system = None
        self.analytics_system = None
        self.cloud_system = None
        self.security_system = None

        logger.info("Phase 8 Integration System initialized")

    def initialize_all_components(self) -> bool:
        """Initialize all Phase 8 components."""
        with self._lock:
            if self._initialized:
                logger.warning("Phase 8 system already initialized")
                return True

            logger.info("Initializing Phase 8 components...")

            success_count = 0
            total_components = 6

            # Initialize Machine Learning Integration
            try:
                from .ml_integration import get_ml_manager, initialize_ml_integration

                initialize_ml_integration()
                self.ml_manager = get_ml_manager()
                self._components["ml_integration"] = IntegrationComponent(
                    name="Machine Learning Integration",
                    status=SystemStatus.HEALTHY,
                    metadata={"models_count": len(self.ml_manager.models)},
                )
                success_count += 1
                logger.info("✓ Machine Learning Integration initialized")
            except Exception as e:
                self._components["ml_integration"] = IntegrationComponent(
                    name="Machine Learning Integration",
                    status=SystemStatus.UNHEALTHY,
                    error_message=str(e),
                )
                logger.error(f"✗ Machine Learning Integration failed: {e}")

            # Initialize Real-time Monitoring
            try:
                from .monitoring import get_monitoring_system, start_monitoring

                self.monitoring_system = get_monitoring_system()
                start_monitoring()
                self._components["monitoring"] = IntegrationComponent(
                    name="Real-time Monitoring",
                    status=SystemStatus.HEALTHY,
                    metadata={
                        "alerts_count": len(self.monitoring_system.alert_manager.alerts)
                    },
                )
                success_count += 1
                logger.info("✓ Real-time Monitoring initialized")
            except Exception as e:
                self._components["monitoring"] = IntegrationComponent(
                    name="Real-time Monitoring",
                    status=SystemStatus.UNHEALTHY,
                    error_message=str(e),
                )
                logger.error(f"✗ Real-time Monitoring failed: {e}")

            # Initialize Enterprise Features
            try:
                from .enterprise import get_enterprise_system, initialize_enterprise

                initialize_enterprise()
                self.enterprise_system = get_enterprise_system()
                self._components["enterprise"] = IntegrationComponent(
                    name="Enterprise Features",
                    status=SystemStatus.HEALTHY,
                    metadata={
                        "tenants_count": len(
                            self.enterprise_system.tenant_manager.tenants
                        )
                    },
                )
                success_count += 1
                logger.info("✓ Enterprise Features initialized")
            except Exception as e:
                self._components["enterprise"] = IntegrationComponent(
                    name="Enterprise Features",
                    status=SystemStatus.UNHEALTHY,
                    error_message=str(e),
                )
                logger.error(f"✗ Enterprise Features failed: {e}")

            # Initialize Advanced Analytics
            try:
                from .analytics import get_analytics_system, initialize_analytics

                initialize_analytics()
                self.analytics_system = get_analytics_system()
                self._components["analytics"] = IntegrationComponent(
                    name="Advanced Analytics",
                    status=SystemStatus.HEALTHY,
                    metadata={
                        "kpis_count": len(self.analytics_system.kpi_manager.kpis)
                    },
                )
                success_count += 1
                logger.info("✓ Advanced Analytics initialized")
            except Exception as e:
                self._components["analytics"] = IntegrationComponent(
                    name="Advanced Analytics",
                    status=SystemStatus.UNHEALTHY,
                    error_message=str(e),
                )
                logger.error(f"✗ Advanced Analytics failed: {e}")

            # Initialize Cloud Integration
            try:
                from .cloud_integration import (
                    get_cloud_system,
                    initialize_cloud_integration,
                )

                initialize_cloud_integration()
                self.cloud_system = get_cloud_system()
                self._components["cloud_integration"] = IntegrationComponent(
                    name="Cloud Integration",
                    status=SystemStatus.HEALTHY,
                    metadata={
                        "pipelines_count": len(
                            self.cloud_system.pipeline_manager.pipelines
                        )
                    },
                )
                success_count += 1
                logger.info("✓ Cloud Integration initialized")
            except Exception as e:
                self._components["cloud_integration"] = IntegrationComponent(
                    name="Cloud Integration",
                    status=SystemStatus.UNHEALTHY,
                    error_message=str(e),
                )
                logger.error(f"✗ Cloud Integration failed: {e}")

            # Initialize Advanced Security
            try:
                from .advanced_security import (
                    get_advanced_security_system,
                    initialize_advanced_security,
                )

                initialize_advanced_security()
                self.security_system = get_advanced_security_system()
                self._components["advanced_security"] = IntegrationComponent(
                    name="Advanced Security",
                    status=SystemStatus.HEALTHY,
                    metadata={
                        "threats_detected": len(
                            self.security_system.threat_detector.threats
                        )
                    },
                )
                success_count += 1
                logger.info("✓ Advanced Security initialized")
            except Exception as e:
                self._components["advanced_security"] = IntegrationComponent(
                    name="Advanced Security",
                    status=SystemStatus.UNHEALTHY,
                    error_message=str(e),
                )
                logger.error(f"✗ Advanced Security failed: {e}")

            # Determine overall system status
            if success_count == total_components:
                overall_status = SystemStatus.HEALTHY
            elif success_count >= total_components * 0.8:
                overall_status = SystemStatus.DEGRADED
            elif success_count >= total_components * 0.5:
                overall_status = SystemStatus.UNHEALTHY
            else:
                overall_status = SystemStatus.CRITICAL

            self._initialized = True
            logger.info(
                f"Phase 8 initialization complete: {success_count}/{total_components} components healthy"
            )
            logger.info(f"Overall system status: {overall_status.value}")

            return success_count > 0

    def get_system_health(self) -> SystemHealth:
        """Get current system health status."""
        with self._lock:
            uptime = time.time() - self._start_time

            # Count operations (simplified)
            total_ops = sum(
                len(comp.metadata.get("operations", []))
                for comp in self._components.values()
            )
            successful_ops = sum(
                len(
                    [
                        op
                        for op in comp.metadata.get("operations", [])
                        if op.get("success", False)
                    ]
                )
                for comp in self._components.values()
            )
            failed_ops = total_ops - successful_ops

            return SystemHealth(
                overall_status=self._get_overall_status(),
                components=list(self._components.values()),
                uptime_seconds=uptime,
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
            )

    def _get_overall_status(self) -> SystemStatus:
        """Determine overall system status based on component statuses."""
        if not self._components:
            return SystemStatus.UNKNOWN

        statuses = [comp.status for comp in self._components.values()]

        if all(status == SystemStatus.HEALTHY for status in statuses):
            return SystemStatus.HEALTHY
        elif any(status == SystemStatus.CRITICAL for status in statuses):
            return SystemStatus.CRITICAL
        elif any(status == SystemStatus.UNHEALTHY for status in statuses):
            return SystemStatus.UNHEALTHY
        else:
            return SystemStatus.DEGRADED

    def generate_comprehensive_report(self) -> IntegrationReport:
        """Generate comprehensive integration report."""
        with self._lock:
            system_health = self.get_system_health()

            # Generate component reports
            component_reports = {}
            for name, comp in self._components.items():
                component_reports[name] = {
                    "status": comp.status.value,
                    "last_check": comp.last_check.isoformat(),
                    "error_message": comp.error_message,
                    "metadata": comp.metadata,
                }

            # Generate summary
            summary = {
                "total_components": len(self._components),
                "healthy_components": len(
                    [
                        c
                        for c in self._components.values()
                        if c.status == SystemStatus.HEALTHY
                    ]
                ),
                "degraded_components": len(
                    [
                        c
                        for c in self._components.values()
                        if c.status == SystemStatus.DEGRADED
                    ]
                ),
                "unhealthy_components": len(
                    [
                        c
                        for c in self._components.values()
                        if c.status == SystemStatus.UNHEALTHY
                    ]
                ),
                "critical_components": len(
                    [
                        c
                        for c in self._components.values()
                        if c.status == SystemStatus.CRITICAL
                    ]
                ),
                "uptime_hours": system_health.uptime_seconds / 3600,
                "success_rate": (
                    system_health.successful_operations
                    / max(system_health.total_operations, 1)
                )
                * 100,
            }

            # Generate recommendations
            recommendations = []
            if summary["critical_components"] > 0:
                recommendations.append(
                    "Address critical component failures immediately"
                )
            if summary["unhealthy_components"] > 0:
                recommendations.append("Investigate unhealthy components")
            if summary["success_rate"] < 95:
                recommendations.append("Improve system reliability")
            if summary["uptime_hours"] < 24:
                recommendations.append("Monitor system stability")

            return IntegrationReport(
                report_type="comprehensive_integration_report",
                system_health=system_health,
                component_reports=component_reports,
                summary=summary,
                recommendations=recommendations,
            )

    def shutdown(self):
        """Gracefully shutdown the Phase 8 system."""
        with self._lock:
            if self._shutdown:
                return

            logger.info("Shutting down Phase 8 system...")

            # Stop monitoring
            if self.monitoring_system:
                try:
                    from .monitoring import stop_monitoring

                    stop_monitoring()
                    logger.info("✓ Monitoring stopped")
                except Exception as e:
                    logger.error(f"✗ Error stopping monitoring: {e}")

            self._shutdown = True
            logger.info("Phase 8 system shutdown complete")


# Global instance
_phase8_system: Optional[Phase8IntegrationSystem] = None
_system_lock = threading.RLock()


def get_phase8_system() -> Phase8IntegrationSystem:
    """Get the global Phase 8 integration system instance."""
    global _phase8_system
    with _system_lock:
        if _phase8_system is None:
            _phase8_system = Phase8IntegrationSystem()
        return _phase8_system


def initialize_phase8() -> bool:
    """Initialize the complete Phase 8 system."""
    system = get_phase8_system()
    return system.initialize_all_components()


def get_phase8_status() -> Dict[str, Any]:
    """Get Phase 8 system status."""
    system = get_phase8_system()
    health = system.get_system_health()

    return {
        "phase": "Phase 8",
        "system_status": health.overall_status.value,
        "component_status": {
            comp.name: comp.status.value for comp in health.components
        },
        "uptime_seconds": health.uptime_seconds,
        "total_operations": health.total_operations,
        "successful_operations": health.successful_operations,
        "failed_operations": health.failed_operations,
        "initialized": system._initialized,
    }


def generate_phase8_report() -> Dict[str, Any]:
    """Generate Phase 8 integration report."""
    system = get_phase8_system()
    report = system.generate_comprehensive_report()

    return {
        "report_type": report.report_type,
        "generated_at": report.generated_at.isoformat(),
        "system_health": {
            "overall_status": report.system_health.overall_status.value,
            "uptime_seconds": report.system_health.uptime_seconds,
            "total_operations": report.system_health.total_operations,
            "successful_operations": report.system_health.successful_operations,
            "failed_operations": report.system_health.failed_operations,
        },
        "component_reports": report.component_reports,
        "summary": report.summary,
        "recommendations": report.recommendations,
    }


if __name__ == "__main__":
    # Initialize Phase 8 when run directly
    print("🚀 Initializing AI-Guard Phase 8: Advanced Features and Integration")
    success = initialize_phase8()

    if success:
        print("✅ Phase 8 initialization successful!")
        status = get_phase8_status()
        print(f"System Status: {status['system_status']}")
        print(f"Components: {len(status['component_status'])}")
    else:
        print("❌ Phase 8 initialization failed!")

    print("\n📊 Phase 8 Status Report:")
    report = generate_phase8_report()
    print(json.dumps(report, indent=2))
