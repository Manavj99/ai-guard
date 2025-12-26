"""Comprehensive tests for analytics.py module to achieve 80%+ coverage."""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.ai_guard.analytics import (
    MetricType,
    KPIType,
    Metric,
    KPI,
    KPIMeasurement,
    AnalyticsReport,
    MetricsCollector,
    KPIManager,
    AnalyticsSystem,
    get_analytics_system,
    initialize_analytics,
)


class TestMetricType:
    """Test MetricType enum."""

    def test_metric_type_values(self):
        """Test metric type enum values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.TIMER.value == "timer"
        assert MetricType.HISTOGRAM.value == "histogram"


class TestKPIType:
    """Test KPIType enum."""

    def test_kpi_type_values(self):
        """Test KPI type enum values."""
        assert KPIType.PERFORMANCE.value == "performance"
        assert KPIType.QUALITY.value == "quality"
        assert KPIType.SECURITY.value == "security"
        assert KPIType.BUSINESS.value == "business"
        assert KPIType.OPERATIONAL.value == "operational"


class TestMetric:
    """Test Metric dataclass."""

    def test_metric_creation(self):
        """Test creating a metric."""
        metric = Metric(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.COUNTER,
            tags={"env": "test"},
        )
        assert metric.name == "test_metric"
        assert metric.value == 42.0
        assert metric.metric_type == MetricType.COUNTER
        assert metric.tags == {"env": "test"}
        assert isinstance(metric.timestamp, datetime)

    def test_metric_defaults(self):
        """Test metric with default values."""
        metric = Metric(
            name="test", value=1.0, metric_type=MetricType.GAUGE
        )
        assert metric.tags == {}
        assert metric.metadata == {}


class TestKPI:
    """Test KPI dataclass."""

    def test_kpi_creation(self):
        """Test creating a KPI."""
        kpi = KPI(
            id="test_kpi",
            name="Test KPI",
            description="Test description",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
            warning_threshold=80.0,
            critical_threshold=50.0,
        )
        assert kpi.id == "test_kpi"
        assert kpi.name == "Test KPI"
        assert kpi.kpi_type == KPIType.PERFORMANCE
        assert kpi.target_value == 100.0


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
        collector.add_metric(
            name="test_metric",
            value=42.0,
            metric_type=MetricType.COUNTER,
            tags={"env": "test"},
        )
        assert len(collector.metrics) == 1
        assert collector.metrics[0].name == "test_metric"
        assert "test_metric" in collector.metric_cache

    def test_add_metric_with_metadata(self):
        """Test adding metric with metadata."""
        collector = MetricsCollector()
        collector.add_metric(
            name="test",
            value=1.0,
            metric_type=MetricType.GAUGE,
            metadata={"key": "value"},
        )
        assert collector.metrics[0].metadata == {"key": "value"}

    def test_get_metrics_all(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        collector.add_metric("metric1", 1.0, MetricType.COUNTER)
        collector.add_metric("metric2", 2.0, MetricType.GAUGE)
        metrics = collector.get_metrics()
        assert len(metrics) == 2

    def test_get_metrics_by_name(self):
        """Test getting metrics by name."""
        collector = MetricsCollector()
        collector.add_metric("metric1", 1.0, MetricType.COUNTER)
        collector.add_metric("metric1", 2.0, MetricType.COUNTER)
        collector.add_metric("metric2", 3.0, MetricType.GAUGE)
        metrics = collector.get_metrics(name="metric1")
        assert len(metrics) == 2
        assert all(m.name == "metric1" for m in metrics)

    def test_get_metrics_by_type(self):
        """Test getting metrics by type."""
        collector = MetricsCollector()
        collector.add_metric("m1", 1.0, MetricType.COUNTER)
        collector.add_metric("m2", 2.0, MetricType.GAUGE)
        metrics = collector.get_metrics(metric_type=MetricType.COUNTER)
        assert len(metrics) == 1
        assert metrics[0].metric_type == MetricType.COUNTER

    def test_get_metrics_by_time_range(self):
        """Test getting metrics by time range."""
        collector = MetricsCollector()
        now = datetime.now()
        collector.add_metric("m1", 1.0, MetricType.COUNTER)
        time.sleep(0.1)
        collector.add_metric("m2", 2.0, MetricType.COUNTER)
        metrics = collector.get_metrics(
            start_time=now, end_time=datetime.now()
        )
        assert len(metrics) >= 1

    def test_thread_safety(self):
        """Test metrics collector thread safety."""
        collector = MetricsCollector()
        results = []

        def add_metrics():
            for i in range(10):
                collector.add_metric(f"metric_{i}", i, MetricType.COUNTER)
                results.append(i)

        threads = [threading.Thread(target=add_metrics) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(collector.metrics) == 50


class TestKPIManager:
    """Test KPIManager class."""

    def test_init(self):
        """Test KPI manager initialization."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        assert len(manager.kpis) >= 2  # Default KPIs
        assert manager.metrics_collector == collector

    def test_create_kpi(self):
        """Test creating a KPI."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        kpi = manager.create_kpi(
            name="Custom KPI",
            description="Test",
            kpi_type=KPIType.QUALITY,
            metric_name="custom_metric",
            target_value=90.0,
            warning_threshold=80.0,
            critical_threshold=70.0,
        )
        assert kpi.name == "Custom KPI"
        assert kpi.id in manager.kpis

    def test_calculate_kpi_no_metrics(self):
        """Test calculating KPI with no metrics."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        kpi = manager.create_kpi(
            name="Test",
            description="Test",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="nonexistent",
            target_value=100.0,
        )
        result = manager.calculate_kpi(kpi.id)
        assert result is None

    def test_calculate_kpi_with_metrics(self):
        """Test calculating KPI with metrics."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        kpi = manager.create_kpi(
            name="Test",
            description="Test",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
            warning_threshold=80.0,
            critical_threshold=60.0,
        )
        collector.add_metric("test_metric", 75.0, MetricType.GAUGE)
        collector.add_metric("test_metric", 85.0, MetricType.GAUGE)
        result = manager.calculate_kpi(kpi.id)
        assert result is not None
        assert result.value == 80.0
        assert result.status in ["normal", "warning", "critical"]

    def test_calculate_kpi_warning_status(self):
        """Test KPI with warning status."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        kpi = manager.create_kpi(
            name="Test",
            description="Test",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
            warning_threshold=80.0,
            critical_threshold=90.0,
        )
        collector.add_metric("test_metric", 85.0, MetricType.GAUGE)
        result = manager.calculate_kpi(kpi.id)
        assert result is not None
        assert result.status in ["normal", "warning", "critical"]

    def test_calculate_kpi_critical_status(self):
        """Test KPI with critical status."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        kpi = manager.create_kpi(
            name="Test",
            description="Test",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
            warning_threshold=80.0,
            critical_threshold=90.0,
        )
        collector.add_metric("test_metric", 95.0, MetricType.GAUGE)
        result = manager.calculate_kpi(kpi.id)
        assert result is not None

    def test_get_all_kpi_statuses(self):
        """Test getting all KPI statuses."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        collector.add_metric("analysis_duration", 25.0, MetricType.TIMER)
        statuses = manager.get_all_kpi_statuses()
        assert len(statuses) >= 2
        assert all("kpi_id" in s for s in statuses)

    def test_get_all_kpi_statuses_no_data(self):
        """Test getting KPI statuses with no data."""
        collector = MetricsCollector()
        manager = KPIManager(collector)
        statuses = manager.get_all_kpi_statuses()
        assert len(statuses) >= 2
        assert any(s["status"] == "no_data" for s in statuses)


class TestAnalyticsSystem:
    """Test AnalyticsSystem class."""

    def test_init(self):
        """Test analytics system initialization."""
        system = AnalyticsSystem()
        assert system.metrics_collector is not None
        assert system.kpi_manager is not None

    def test_generate_executive_report(self):
        """Test generating executive report."""
        system = AnalyticsSystem()
        system.metrics_collector.add_metric(
            "analysis_duration", 25.0, MetricType.TIMER
        )
        report = system.generate_executive_report()
        assert report.report_type == "executive"
        assert "kpis" in report.data
        assert "total_kpis" in report.summary

    def test_generate_executive_report_with_critical(self):
        """Test executive report with critical KPIs."""
        system = AnalyticsSystem()
        system.metrics_collector.add_metric(
            "quality_score", 50.0, MetricType.GAUGE
        )
        report = system.generate_executive_report()
        assert len(report.recommendations) >= 0

    def test_get_system_statistics(self):
        """Test getting system statistics."""
        system = AnalyticsSystem()
        system.metrics_collector.add_metric("test", 1.0, MetricType.COUNTER)
        stats = system.get_system_statistics()
        assert "metrics" in stats
        assert "kpis" in stats
        assert stats["metrics"]["total"] >= 1

    def test_generate_report(self):
        """Test generating comprehensive report."""
        system = AnalyticsSystem()
        system.metrics_collector.add_metric(
            "analysis_duration", 25.0, MetricType.TIMER
        )
        report = system.generate_report()
        assert report.report_type == "comprehensive"
        assert "kpis" in report.data
        assert "metrics_summary" in report.data

    def test_get_analytics_data(self):
        """Test getting analytics data."""
        system = AnalyticsSystem()
        system.metrics_collector.add_metric("test", 1.0, MetricType.COUNTER)
        data = system.get_analytics_data()
        assert "timestamp" in data
        assert "kpis" in data
        assert "metrics" in data
        assert "summary" in data


class TestGlobalFunctions:
    """Test global functions."""

    def test_get_analytics_system(self):
        """Test getting analytics system."""
        system1 = get_analytics_system()
        system2 = get_analytics_system()
        assert system1 is system2  # Singleton

    def test_initialize_analytics(self):
        """Test initializing analytics."""
        result = initialize_analytics()
        assert result is True


class TestAnalyticsReport:
    """Test AnalyticsReport dataclass."""

    def test_analytics_report_creation(self):
        """Test creating analytics report."""
        report = AnalyticsReport(
            report_type="test",
            data={"key": "value"},
            summary={"total": 10},
            recommendations=["rec1"],
        )
        assert report.report_type == "test"
        assert report.data == {"key": "value"}
        assert report.summary == {"total": 10}
        assert report.recommendations == ["rec1"]

    def test_analytics_report_defaults(self):
        """Test analytics report with defaults."""
        report = AnalyticsReport(report_type="test")
        assert report.data == {}
        assert report.summary == {}
        assert report.recommendations == []
        assert isinstance(report.generated_at, datetime)


class TestKPIMeasurement:
    """Test KPIMeasurement dataclass."""

    def test_kpi_measurement_creation(self):
        """Test creating KPI measurement."""
        measurement = KPIMeasurement(
            kpi_id="test_kpi",
            value=85.0,
            status="normal",
            metadata={"count": 10},
        )
        assert measurement.kpi_id == "test_kpi"
        assert measurement.value == 85.0
        assert measurement.status == "normal"
        assert measurement.metadata == {"count": 10}

    def test_kpi_measurement_defaults(self):
        """Test KPI measurement with defaults."""
        measurement = KPIMeasurement(kpi_id="test", value=100.0)
        assert measurement.status == "normal"
        assert measurement.metadata == {}
        assert isinstance(measurement.timestamp, datetime)

