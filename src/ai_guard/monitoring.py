"""Real-time Monitoring and Alerting System for AI-Guard."""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"
    CONSOLE = "console"


class HealthStatus(Enum):
    """System health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class Metric:
    """System metric."""

    name: str
    value: Union[float, int, str]
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert configuration."""

    name: str
    description: str
    level: AlertLevel
    condition: str
    threshold: float
    channels: List[AlertChannel]
    id: str = field(default_factory=lambda: f"alert_{int(time.time())}")
    cooldown_seconds: int = 300
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertEvent:
    """Alert event."""

    alert_id: str
    message: str
    level: AlertLevel
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and stores system metrics."""

    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = threading.RLock()
        self.metrics: List[Metric] = []
        self.metric_cache: Dict[str, List[Metric]] = {}

        logger.info("Metrics Collector initialized")

    def add_metric(self, metric: Metric) -> None:
        """Add a metric."""
        with self._lock:
            self.metrics.append(metric)

            # Update cache
            if metric.name not in self.metric_cache:
                self.metric_cache[metric.name] = []
            self.metric_cache[metric.name].append(metric)

            logger.debug(f"Added metric: {metric.name} = {metric.value}")

    def get_metrics(
        self,
        name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Metric]:
        """Get metrics with optional filters."""
        with self._lock:
            if name:
                metrics = self.metric_cache.get(name, []).copy()
            else:
                metrics = self.metrics.copy()

            # Apply filters
            if start_time:
                metrics = [m for m in metrics if m.timestamp >= start_time]
            if end_time:
                metrics = [m for m in metrics if m.timestamp <= end_time]

            return metrics

    def get_latest_metric(self, name: str) -> Optional[Metric]:
        """Get the latest metric for a given name."""
        with self._lock:
            metrics = self.metric_cache.get(name, [])
            return metrics[-1] if metrics else None


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self):
        """Initialize the alert manager."""
        self._lock = threading.RLock()
        self.alerts: Dict[str, Alert] = {}
        self.alert_events: List[AlertEvent] = []
        self.rules: Dict[str, Dict[str, Any]] = {}

        logger.info("Alert Manager initialized")

    def add_alert(self, alert: Alert) -> None:
        """Add an alert."""
        with self._lock:
            self.alerts[alert.id] = alert
            logger.info(f"Added alert: {alert.name}")

    def check_alerts(self, metrics_collector: MetricsCollector) -> List[AlertEvent]:
        """Check all alerts against current metrics."""
        with self._lock:
            triggered_events = []

            for alert in self.alerts.values():
                if not alert.enabled:
                    continue

                # Check cooldown
                if alert.last_triggered:
                    time_since_last = datetime.now() - alert.last_triggered
                    if time_since_last.total_seconds() < alert.cooldown_seconds:
                        continue

                # Get relevant metric
                metric_name = alert.condition.split()[0]  # Simple parsing
                latest_metric = metrics_collector.get_latest_metric(metric_name)

                if not latest_metric:
                    continue

                # Check condition (simplified)
                metric_value = latest_metric.value
                if isinstance(metric_value, (int, float)):
                    if ">" in alert.condition:
                        if metric_value > alert.threshold:
                            event = self._trigger_alert(alert, metric_value)
                            triggered_events.append(event)
                    elif "<" in alert.condition:
                        if metric_value < alert.threshold:
                            event = self._trigger_alert(alert, metric_value)
                            triggered_events.append(event)

            return triggered_events

    def _trigger_alert(self, alert: Alert, metric_value: float) -> AlertEvent:
        """Trigger an alert."""
        alert.last_triggered = datetime.now()

        event = AlertEvent(
            alert_id=alert.id,
            message=f"{alert.name}: {alert.description} (Current: {metric_value})",
            level=alert.level,
            metadata={"metric_value": metric_value, "threshold": alert.threshold},
        )

        self.alert_events.append(event)

        # Send notifications
        self._send_notifications(event, alert)

        logger.warning(f"Alert triggered: {alert.name}")
        return event

    def _send_notifications(self, event: AlertEvent, alert: Alert) -> None:
        """Send notifications through configured channels."""
        for channel in alert.channels:
            if channel == AlertChannel.CONSOLE:
                print(f"[{event.level.value.upper()}] {event.message}")
            elif channel == AlertChannel.LOG:
                logger.warning(f"ALERT: {event.message}")
            # Other channels would be implemented here

    def create_alert(self, title: str, message: str, severity: str) -> Alert:
        """Create a new alert."""
        with self._lock:
            alert_id = f"alert_{int(time.time())}"
            level = AlertLevel.WARNING
            if severity == "high":
                level = AlertLevel.ERROR
            elif severity == "critical":
                level = AlertLevel.CRITICAL
            elif severity == "info":
                level = AlertLevel.INFO

            alert = Alert(
                id=alert_id,
                name=title,
                description=message,
                level=level,
                condition="manual",
                threshold=0.0,
                channels=[AlertChannel.CONSOLE],
            )

            self.alerts[alert_id] = alert
            logger.info(f"Created alert: {title}")
            return alert


class MonitoringSystem:
    """Main monitoring system."""

    def __init__(self):
        """Initialize the monitoring system."""
        self._lock = threading.RLock()
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self._running = False
        self._monitoring_thread: Optional[threading.Thread] = None

        logger.info("Monitoring System initialized")

    def start_monitoring(self) -> None:
        """Start the monitoring system."""
        with self._lock:
            if self._running:
                logger.warning("Monitoring already running")
                return

            self._running = True
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop, daemon=True
            )
            self._monitoring_thread.start()
            logger.info("Monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        with self._lock:
            if not self._running:
                return

            self._running = False
            if self._monitoring_thread:
                self._monitoring_thread.join(timeout=5)
            logger.info("Monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                # Check alerts
                events = self.alert_manager.check_alerts(self.metrics_collector)

                # Collect system metrics
                self._collect_system_metrics()

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(30)  # Wait longer on error

    def _collect_system_metrics(self) -> None:
        """Collect basic system metrics."""
        try:
            import psutil

            # CPU usage
            cpu_metric = Metric(
                name="cpu_usage",
                value=psutil.cpu_percent(),
                unit="percent",
                tags={"source": "system"},
            )
            self.metrics_collector.add_metric(cpu_metric)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_metric = Metric(
                name="memory_usage",
                value=memory.percent,
                unit="percent",
                tags={"source": "system"},
            )
            self.metrics_collector.add_metric(memory_metric)

            # Available memory
            available_memory_metric = Metric(
                name="memory_available",
                value=memory.available / (1024**3),  # GB
                unit="GB",
                tags={"source": "system"},
            )
            self.metrics_collector.add_metric(available_memory_metric)

        except ImportError:
            # psutil not available, use dummy metrics
            cpu_metric = Metric(
                name="cpu_usage", value=25.0, unit="percent", tags={"source": "dummy"}
            )
            self.metrics_collector.add_metric(cpu_metric)

            memory_metric = Metric(
                name="memory_usage",
                value=60.0,
                unit="percent",
                tags={"source": "dummy"},
            )
            self.metrics_collector.add_metric(memory_metric)

            available_memory_metric = Metric(
                name="memory_available", value=2.5, unit="GB", tags={"source": "dummy"}
            )
            self.metrics_collector.add_metric(available_memory_metric)


# Global instances
_monitoring_system: Optional[MonitoringSystem] = None
_monitoring_lock = threading.RLock()


def get_monitoring_system() -> MonitoringSystem:
    """Get the global monitoring system instance."""
    global _monitoring_system
    with _monitoring_lock:
        if _monitoring_system is None:
            _monitoring_system = MonitoringSystem()
        return _monitoring_system


def start_monitoring() -> None:
    """Start the monitoring system."""
    system = get_monitoring_system()
    system.start_monitoring()


def stop_monitoring() -> None:
    """Stop the monitoring system."""
    system = get_monitoring_system()
    system.stop_monitoring()


if __name__ == "__main__":
    # Test monitoring system
    print("📊 Testing AI-Guard Monitoring System")

    monitoring_system = get_monitoring_system()

    # Add some test metrics
    test_metric = Metric(
        name="test_metric", value=42.0, unit="count", tags={"environment": "test"}
    )
    monitoring_system.metrics_collector.add_metric(test_metric)

    # Create a test alert
    test_alert = Alert(
        id="test_alert",
        name="Test Alert",
        description="Test alert for monitoring",
        level=AlertLevel.WARNING,
        condition="test_metric > 40",
        threshold=40.0,
        channels=[AlertChannel.CONSOLE],
    )
    monitoring_system.alert_manager.add_alert(test_alert)

    # Check alerts
    events = monitoring_system.alert_manager.check_alerts(
        monitoring_system.metrics_collector
    )
    print(f"✅ Monitoring test: {len(events)} alerts triggered")

    # Start monitoring
    start_monitoring()
    print("✅ Monitoring started")

    time.sleep(2)

    # Stop monitoring
    stop_monitoring()
    print("✅ Monitoring stopped")
