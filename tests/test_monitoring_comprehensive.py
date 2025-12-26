"""Comprehensive tests for monitoring.py module to achieve 80%+ coverage."""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock

from src.ai_guard.monitoring import (
    AlertLevel,
    AlertChannel,
    HealthStatus,
    Metric,
    Alert,
    AlertEvent,
    MetricsCollector,
    AlertManager,
    MonitoringSystem,
    get_monitoring_system,
    start_monitoring,
    stop_monitoring,
)


class TestEnums:
    """Test enum classes."""

    def test_alert_level_values(self):
        """Test AlertLevel enum values."""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.ERROR.value == "error"
        assert AlertLevel.CRITICAL.value == "critical"

    def test_alert_channel_values(self):
        """Test AlertChannel enum values."""
        assert AlertChannel.EMAIL.value == "email"
        assert AlertChannel.SLACK.value == "slack"
        assert AlertChannel.WEBHOOK.value == "webhook"
        assert AlertChannel.LOG.value == "log"
        assert AlertChannel.CONSOLE.value == "console"

    def test_health_status_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.CRITICAL.value == "critical"


class TestMetric:
    """Test Metric dataclass."""

    def test_metric_creation(self):
        """Test creating a metric."""
        metric = Metric(
            name="cpu_usage",
            value=75.5,
            unit="percent",
            tags={"source": "system"},
        )
        assert metric.name == "cpu_usage"
        assert metric.value == 75.5
        assert metric.unit == "percent"
        assert metric.tags == {"source": "system"}
        assert isinstance(metric.timestamp, datetime)

    def test_metric_defaults(self):
        """Test metric with default values."""
        metric = Metric(name="test", value=42, unit="count")
        assert metric.tags == {}
        assert metric.metadata == {}


class TestAlert:
    """Test Alert dataclass."""

    def test_alert_creation(self):
        """Test creating an alert."""
        alert = Alert(
            name="High CPU",
            description="CPU usage is high",
            level=AlertLevel.WARNING,
            condition="cpu_usage > 80",
            threshold=80.0,
            channels=[AlertChannel.EMAIL, AlertChannel.CONSOLE],
        )
        assert alert.name == "High CPU"
        assert alert.level == AlertLevel.WARNING
        assert alert.threshold == 80.0
        assert alert.enabled is True
        assert alert.cooldown_seconds == 300

    def test_alert_defaults(self):
        """Test alert with default values."""
        alert = Alert(
            name="Test",
            description="Test alert",
            level=AlertLevel.INFO,
            condition="test > 0",
            threshold=0.0,
            channels=[],
        )
        assert alert.enabled is True
        assert isinstance(alert.created_at, datetime)


class TestAlertEvent:
    """Test AlertEvent dataclass."""

    def test_alert_event_creation(self):
        """Test creating an alert event."""
        event = AlertEvent(
            alert_id="alert_123",
            message="CPU is high",
            level=AlertLevel.WARNING,
            metadata={"value": 85.0},
        )
        assert event.alert_id == "alert_123"
        assert event.message == "CPU is high"
        assert event.level == AlertLevel.WARNING
        assert event.metadata == {"value": 85.0}
        assert isinstance(event.timestamp, datetime)


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_init(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()
        assert collector.metrics == []
        assert collector.metric_cache == {}

    def test_add_metric(self):
        """Test adding a metric."""
        collector = MetricsCollector()
        metric = Metric(name="test_metric", value=42.0, unit="count")
        collector.add_metric(metric)
        assert len(collector.metrics) == 1
        assert "test_metric" in collector.metric_cache

    def test_get_metrics_all(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        collector.add_metric(Metric(name="m1", value=1.0, unit="count"))
        collector.add_metric(Metric(name="m2", value=2.0, unit="count"))
        metrics = collector.get_metrics()
        assert len(metrics) == 2

    def test_get_metrics_by_name(self):
        """Test getting metrics by name."""
        collector = MetricsCollector()
        collector.add_metric(Metric(name="m1", value=1.0, unit="count"))
        collector.add_metric(Metric(name="m1", value=2.0, unit="count"))
        collector.add_metric(Metric(name="m2", value=3.0, unit="count"))
        metrics = collector.get_metrics(name="m1")
        assert len(metrics) == 2
        assert all(m.name == "m1" for m in metrics)

    def test_get_metrics_by_time_range(self):
        """Test getting metrics by time range."""
        collector = MetricsCollector()
        start = datetime.now()
        collector.add_metric(Metric(name="m1", value=1.0, unit="count"))
        time.sleep(0.1)
        collector.add_metric(Metric(name="m2", value=2.0, unit="count"))
        end = datetime.now()
        metrics = collector.get_metrics(start_time=start, end_time=end)
        assert len(metrics) >= 1

    def test_get_latest_metric(self):
        """Test getting latest metric."""
        collector = MetricsCollector()
        collector.add_metric(Metric(name="m1", value=1.0, unit="count"))
        time.sleep(0.01)
        collector.add_metric(Metric(name="m1", value=2.0, unit="count"))
        latest = collector.get_latest_metric("m1")
        assert latest is not None
        assert latest.value == 2.0

    def test_get_latest_metric_nonexistent(self):
        """Test getting latest metric that doesn't exist."""
        collector = MetricsCollector()
        latest = collector.get_latest_metric("nonexistent")
        assert latest is None


class TestAlertManager:
    """Test AlertManager class."""

    def test_init(self):
        """Test alert manager initialization."""
        manager = AlertManager()
        assert manager.alerts == {}
        assert manager.alert_events == []
        assert manager.rules == {}

    def test_add_alert(self):
        """Test adding an alert."""
        manager = AlertManager()
        alert = Alert(
            name="Test",
            description="Test alert",
            level=AlertLevel.WARNING,
            condition="test > 0",
            threshold=0.0,
            channels=[AlertChannel.CONSOLE],
        )
        manager.add_alert(alert)
        assert alert.id in manager.alerts

    def test_check_alerts_no_alerts(self):
        """Test checking alerts with no alerts configured."""
        manager = AlertManager()
        collector = MetricsCollector()
        events = manager.check_alerts(collector)
        assert events == []

    def test_check_alerts_disabled(self):
        """Test checking disabled alerts."""
        manager = AlertManager()
        alert = Alert(
            name="Test",
            description="Test",
            level=AlertLevel.WARNING,
            condition="test > 0",
            threshold=0.0,
            channels=[AlertChannel.CONSOLE],
            enabled=False,
        )
        manager.add_alert(alert)
        collector = MetricsCollector()
        events = manager.check_alerts(collector)
        assert events == []

    def test_check_alerts_triggered_greater_than(self):
        """Test alert triggered with > condition."""
        manager = AlertManager()
        alert = Alert(
            name="High CPU",
            description="CPU is high",
            level=AlertLevel.WARNING,
            condition="cpu_usage > 80",
            threshold=80.0,
            channels=[AlertChannel.CONSOLE],
        )
        manager.add_alert(alert)
        collector = MetricsCollector()
        collector.add_metric(Metric(name="cpu_usage", value=85.0, unit="percent"))
        events = manager.check_alerts(collector)
        assert len(events) == 1
        assert events[0].alert_id == alert.id

    def test_check_alerts_triggered_less_than(self):
        """Test alert triggered with < condition."""
        manager = AlertManager()
        alert = Alert(
            name="Low Memory",
            description="Memory is low",
            level=AlertLevel.WARNING,
            condition="memory_available < 1",
            threshold=1.0,
            channels=[AlertChannel.CONSOLE],
        )
        manager.add_alert(alert)
        collector = MetricsCollector()
        collector.add_metric(Metric(name="memory_available", value=0.5, unit="GB"))
        events = manager.check_alerts(collector)
        assert len(events) == 1

    def test_check_alerts_cooldown(self):
        """Test alert cooldown period."""
        manager = AlertManager()
        alert = Alert(
            name="Test",
            description="Test",
            level=AlertLevel.WARNING,
            condition="test > 0",
            threshold=0.0,
            channels=[AlertChannel.CONSOLE],
            cooldown_seconds=3600,
        )
        alert.last_triggered = datetime.now()
        manager.add_alert(alert)
        collector = MetricsCollector()
        collector.add_metric(Metric(name="test", value=1.0, unit="count"))
        events = manager.check_alerts(collector)
        assert len(events) == 0  # Should be in cooldown

    def test_create_alert(self):
        """Test creating an alert."""
        manager = AlertManager()
        alert = manager.create_alert("Test Alert", "Test message", "warning")
        assert alert.name == "Test Alert"
        assert alert.level == AlertLevel.WARNING
        assert alert.id in manager.alerts

    def test_create_alert_critical(self):
        """Test creating critical alert."""
        manager = AlertManager()
        alert = manager.create_alert("Critical", "Message", "critical")
        assert alert.level == AlertLevel.CRITICAL

    def test_create_alert_error(self):
        """Test creating error alert."""
        manager = AlertManager()
        alert = manager.create_alert("Error", "Message", "high")
        assert alert.level == AlertLevel.ERROR

    def test_create_alert_info(self):
        """Test creating info alert."""
        manager = AlertManager()
        alert = manager.create_alert("Info", "Message", "info")
        assert alert.level == AlertLevel.INFO

    def test_send_notifications_console(self):
        """Test sending console notifications."""
        manager = AlertManager()
        event = AlertEvent(
            alert_id="test", message="Test", level=AlertLevel.WARNING
        )
        alert = Alert(
            name="Test",
            description="Test",
            level=AlertLevel.WARNING,
            condition="test > 0",
            threshold=0.0,
            channels=[AlertChannel.CONSOLE],
        )
        with patch("builtins.print") as mock_print:
            manager._send_notifications(event, alert)
            mock_print.assert_called_once()

    def test_send_notifications_log(self):
        """Test sending log notifications."""
        manager = AlertManager()
        event = AlertEvent(
            alert_id="test", message="Test", level=AlertLevel.WARNING
        )
        alert = Alert(
            name="Test",
            description="Test",
            level=AlertLevel.WARNING,
            condition="test > 0",
            threshold=0.0,
            channels=[AlertChannel.LOG],
        )
        manager._send_notifications(event, alert)


class TestMonitoringSystem:
    """Test MonitoringSystem class."""

    def test_init(self):
        """Test monitoring system initialization."""
        system = MonitoringSystem()
        assert system.metrics_collector is not None
        assert system.alert_manager is not None
        assert system._running is False

    def test_start_monitoring(self):
        """Test starting monitoring."""
        system = MonitoringSystem()
        system.start_monitoring()
        assert system._running is True
        assert system._monitoring_thread is not None
        system.stop_monitoring()

    def test_start_monitoring_already_running(self):
        """Test starting monitoring when already running."""
        system = MonitoringSystem()
        system.start_monitoring()
        system.start_monitoring()  # Should not crash
        system.stop_monitoring()

    def test_stop_monitoring(self):
        """Test stopping monitoring."""
        system = MonitoringSystem()
        system.start_monitoring()
        system.stop_monitoring()
        assert system._running is False

    def test_stop_monitoring_not_running(self):
        """Test stopping monitoring when not running."""
        system = MonitoringSystem()
        system.stop_monitoring()  # Should not crash

    @patch("src.ai_guard.monitoring.psutil")
    def test_collect_system_metrics_with_psutil(self, mock_psutil_module):
        """Test collecting system metrics with psutil."""
        try:
            import psutil
            # If psutil is available, test with real module
            system = MonitoringSystem()
            system._collect_system_metrics()
            assert len(system.metrics_collector.metrics) >= 3
        except ImportError:
            # If psutil not available, test with mock
            mock_cpu = MagicMock(return_value=75.5)
            mock_memory = MagicMock()
            mock_memory.percent = 60.0
            mock_memory.available = 4 * 1024**3  # 4 GB
            mock_psutil_module.cpu_percent = mock_cpu
            mock_psutil_module.virtual_memory = MagicMock(return_value=mock_memory)

            system = MonitoringSystem()
            system._collect_system_metrics()

            assert len(system.metrics_collector.metrics) >= 3
            cpu_metrics = [
                m for m in system.metrics_collector.metrics if m.name == "cpu_usage"
            ]
            assert len(cpu_metrics) > 0

    def test_collect_system_metrics_without_psutil(self):
        """Test collecting system metrics without psutil."""
        with patch("builtins.__import__", side_effect=ImportError):
            system = MonitoringSystem()
            system._collect_system_metrics()
            assert len(system.metrics_collector.metrics) >= 3


class TestGlobalFunctions:
    """Test global functions."""

    def test_get_monitoring_system(self):
        """Test getting monitoring system."""
        system1 = get_monitoring_system()
        system2 = get_monitoring_system()
        assert system1 is system2  # Singleton

    def test_start_monitoring_function(self):
        """Test start_monitoring function."""
        stop_monitoring()  # Ensure stopped
        start_monitoring()
        system = get_monitoring_system()
        assert system._running is True
        stop_monitoring()

    def test_stop_monitoring_function(self):
        """Test stop_monitoring function."""
        start_monitoring()
        stop_monitoring()
        system = get_monitoring_system()
        assert system._running is False

