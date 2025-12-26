"""Advanced Analytics and Business Intelligence for AI-Guard."""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    TIMER = "timer"
    HISTOGRAM = "histogram"


class KPIType(Enum):
    """KPI types."""

    PERFORMANCE = "performance"
    QUALITY = "quality"
    SECURITY = "security"
    BUSINESS = "business"
    OPERATIONAL = "operational"


@dataclass
class Metric:
    """Analytics metric."""

    name: str
    value: Union[float, int]
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KPI:
    """Key Performance Indicator."""

    id: str
    name: str
    description: str
    kpi_type: KPIType
    metric_name: str
    target_value: float
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KPIMeasurement:
    """KPI measurement result."""

    kpi_id: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "normal"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsReport:
    """Analytics report."""

    report_type: str
    generated_at: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class MetricsCollector:
    """Collects and manages analytics metrics."""

    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = threading.RLock()
        self.metrics: List[Metric] = []
        self.metric_cache: Dict[str, List[Metric]] = {}
        logger.info("Analytics Metrics Collector initialized")

    def add_metric(
        self,
        name: str,
        value: Union[float, int],
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a metric."""
        with self._lock:
            metric = Metric(
                name=name,
                value=value,
                metric_type=metric_type,
                tags=tags or {},
                metadata=metadata or {},
            )

            self.metrics.append(metric)

            if name not in self.metric_cache:
                self.metric_cache[name] = []
            self.metric_cache[name].append(metric)

            logger.debug(f"Added metric: {name} = {value}")

    def get_metrics(
        self,
        name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Metric]:
        """Get metrics with optional filters."""
        with self._lock:
            if name:
                metrics = self.metric_cache.get(name, []).copy()
            else:
                metrics = self.metrics.copy()

            if metric_type:
                metrics = [m for m in metrics if m.metric_type == metric_type]
            if start_time:
                metrics = [m for m in metrics if m.timestamp >= start_time]
            if end_time:
                metrics = [m for m in metrics if m.timestamp <= end_time]

            return metrics


class KPIManager:
    """Manages KPIs and their measurements."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize the KPI manager."""
        self._lock = threading.RLock()
        self.metrics_collector = metrics_collector
        self.kpis: Dict[str, KPI] = {}
        self.measurements: List[KPIMeasurement] = []
        self._create_default_kpis()
        logger.info("KPI Manager initialized")

    def _create_default_kpis(self):
        """Create default KPIs."""
        default_kpis = [
            {
                "name": "Analysis Performance",
                "description": "Average time to complete code analysis",
                "kpi_type": KPIType.PERFORMANCE,
                "metric_name": "analysis_duration",
                "target_value": 30.0,
                "warning_threshold": 45.0,
                "critical_threshold": 60.0,
            },
            {
                "name": "Code Quality Score",
                "description": "Average code quality score",
                "kpi_type": KPIType.QUALITY,
                "metric_name": "quality_score",
                "target_value": 85.0,
                "warning_threshold": 70.0,
                "critical_threshold": 60.0,
            },
        ]

        for kpi_data in default_kpis:
            self.create_kpi(**kpi_data)

    def create_kpi(
        self,
        name: str,
        description: str,
        kpi_type: KPIType,
        metric_name: str,
        target_value: float,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
    ) -> KPI:
        """Create a new KPI."""
        with self._lock:
            kpi_id = f"{kpi_type.value}_{name.lower().replace(' ', '_')}"
            kpi = KPI(
                id=kpi_id,
                name=name,
                description=description,
                kpi_type=kpi_type,
                metric_name=metric_name,
                target_value=target_value,
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
            )

            self.kpis[kpi_id] = kpi
            logger.info(f"Created KPI: {name}")
            return kpi

    def calculate_kpi(self, kpi_id: str) -> Optional[KPIMeasurement]:
        """Calculate current value for a KPI."""
        with self._lock:
            kpi = self.kpis.get(kpi_id)
            if not kpi:
                return None

            recent_metrics = self.metrics_collector.get_metrics(
                name=kpi.metric_name, start_time=datetime.now() - timedelta(hours=1)
            )

            if not recent_metrics:
                return None

            values = [
                m.value for m in recent_metrics if isinstance(m.value, (int, float))
            ]
            if not values:
                return None

            avg_value = sum(values) / len(values)

            status = "normal"
            if (
                kpi.critical_threshold is not None
                and avg_value >= kpi.critical_threshold
            ):
                status = "critical"
            elif (
                kpi.warning_threshold is not None and avg_value >= kpi.warning_threshold
            ):
                status = "warning"

            measurement = KPIMeasurement(
                kpi_id=kpi_id,
                value=avg_value,
                status=status,
                metadata={"sample_count": len(values)},
            )

            self.measurements.append(measurement)
            kpi.last_updated = datetime.now()

            return measurement

    def get_all_kpi_statuses(self) -> List[Dict[str, Any]]:
        """Get status for all KPIs."""
        with self._lock:
            statuses = []
            for kpi_id, kpi in self.kpis.items():
                measurement = self.calculate_kpi(kpi_id)
                if measurement:
                    statuses.append(
                        {
                            "kpi_id": kpi_id,
                            "name": kpi.name,
                            "value": measurement.value,
                            "status": measurement.status,
                            "target_value": kpi.target_value,
                            "kpi_type": kpi.kpi_type.value,
                        }
                    )
                else:
                    statuses.append(
                        {
                            "kpi_id": kpi_id,
                            "name": kpi.name,
                            "value": None,
                            "status": "no_data",
                            "target_value": kpi.target_value,
                            "kpi_type": kpi.kpi_type.value,
                        }
                    )
            return statuses


class AnalyticsSystem:
    """Main analytics system."""

    def __init__(self):
        """Initialize the analytics system."""
        self._lock = threading.RLock()
        self.metrics_collector = MetricsCollector()
        self.kpi_manager = KPIManager(self.metrics_collector)
        logger.info("Analytics System initialized")

    def generate_executive_report(self) -> AnalyticsReport:
        """Generate executive analytics report."""
        with self._lock:
            kpi_statuses = self.kpi_manager.get_all_kpi_statuses()

            total_kpis = len(kpi_statuses)
            healthy_kpis = len(
                [kpi for kpi in kpi_statuses if kpi["status"] == "normal"]
            )
            warning_kpis = len(
                [kpi for kpi in kpi_statuses if kpi["status"] == "warning"]
            )
            critical_kpis = len(
                [kpi for kpi in kpi_statuses if kpi["status"] == "critical"]
            )

            recommendations = []
            if critical_kpis > 0:
                recommendations.append("Address critical KPI issues immediately")
            if warning_kpis > 0:
                recommendations.append("Monitor warning KPIs closely")

            return AnalyticsReport(
                report_type="executive",
                data={"kpis": kpi_statuses},
                summary={
                    "total_kpis": total_kpis,
                    "healthy_kpis": healthy_kpis,
                    "warning_kpis": warning_kpis,
                    "critical_kpis": critical_kpis,
                    "health_percentage": (healthy_kpis / max(total_kpis, 1)) * 100,
                },
                recommendations=recommendations,
            )

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get analytics system statistics."""
        with self._lock:
            return {
                "metrics": {
                    "total": len(self.metrics_collector.metrics),
                    "unique_names": len(self.metrics_collector.metric_cache),
                },
                "kpis": {
                    "total": len(self.kpi_manager.kpis),
                    "measurements": len(self.kpi_manager.measurements),
                },
            }

    def generate_report(self) -> AnalyticsReport:
        """Generate a comprehensive analytics report."""
        with self._lock:
            kpi_statuses = self.kpi_manager.get_all_kpi_statuses()

            total_kpis = len(kpi_statuses)
            healthy_kpis = len(
                [kpi for kpi in kpi_statuses if kpi["status"] == "normal"]
            )
            warning_kpis = len(
                [kpi for kpi in kpi_statuses if kpi["status"] == "warning"]
            )
            critical_kpis = len(
                [kpi for kpi in kpi_statuses if kpi["status"] == "critical"]
            )

            recommendations = []
            if critical_kpis > 0:
                recommendations.append("Address critical KPI issues immediately")
            if warning_kpis > 0:
                recommendations.append("Monitor warning KPIs closely")
            if healthy_kpis == total_kpis and total_kpis > 0:
                recommendations.append(
                    "All KPIs are healthy - maintain current performance"
                )

            return AnalyticsReport(
                report_type="comprehensive",
                data={
                    "kpis": kpi_statuses,
                    "metrics_summary": self.get_system_statistics(),
                },
                summary={
                    "total_kpis": total_kpis,
                    "healthy_kpis": healthy_kpis,
                    "warning_kpis": warning_kpis,
                    "critical_kpis": critical_kpis,
                    "health_percentage": (healthy_kpis / max(total_kpis, 1)) * 100,
                },
                recommendations=recommendations,
            )

    def get_analytics_data(self) -> Dict[str, Any]:
        """Get comprehensive analytics data for dashboard."""
        with self._lock:
            kpi_statuses = self.kpi_manager.get_all_kpi_statuses()
            system_stats = self.get_system_statistics()

            return {
                "timestamp": datetime.now().isoformat(),
                "kpis": kpi_statuses,
                "metrics": system_stats["metrics"],
                "summary": {
                    "total_kpis": len(kpi_statuses),
                    "healthy_kpis": len(
                        [kpi for kpi in kpi_statuses if kpi["status"] == "normal"]
                    ),
                    "warning_kpis": len(
                        [kpi for kpi in kpi_statuses if kpi["status"] == "warning"]
                    ),
                    "critical_kpis": len(
                        [kpi for kpi in kpi_statuses if kpi["status"] == "critical"]
                    ),
                },
            }


# Global instance
_analytics_system: Optional[AnalyticsSystem] = None
_analytics_lock = threading.RLock()


def get_analytics_system() -> AnalyticsSystem:
    """Get the global analytics system instance."""
    global _analytics_system
    with _analytics_lock:
        if _analytics_system is None:
            _analytics_system = AnalyticsSystem()
        return _analytics_system


def initialize_analytics() -> bool:
    """Initialize the analytics system."""
    try:
        get_analytics_system()
        logger.info("Analytics system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Analytics system initialization failed: {e}")
        return False


if __name__ == "__main__":
    print("📊 Testing AI-Guard Advanced Analytics")

    success = initialize_analytics()
    if success:
        print("✅ Analytics system initialized successfully")

        analytics_system = get_analytics_system()

        analytics_system.metrics_collector.add_metric(
            name="analysis_duration",
            value=25.5,
            metric_type=MetricType.TIMER,
            tags={"environment": "test"},
        )

        stats = analytics_system.get_system_statistics()
        print(f"📊 Analytics Statistics: {json.dumps(stats, indent=2)}")
    else:
        print("❌ Analytics system initialization failed")
