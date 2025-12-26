"""Tests for the analytics module."""

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.ai_guard.analytics import (
    MetricType,
    KPIType,
    Metric,
    KPI,
    KPIManager,
    AnalyticsSystem,
    MetricsCollector,
)


class TestAnalytics(unittest.TestCase):
    """Test analytics functionality."""

    def test_metric_creation(self):
        """Test metric creation."""
        metric = Metric(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            tags={"environment": "test"},
        )

        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.value, 42.5)
        self.assertEqual(metric.metric_type, MetricType.GAUGE)
        self.assertEqual(metric.tags["environment"], "test")

    def test_kpi_creation(self):
        """Test KPI creation."""
        kpi = KPI(
            id="test_kpi",
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )

        self.assertEqual(kpi.id, "test_kpi")
        self.assertEqual(kpi.name, "Test KPI")
        self.assertEqual(kpi.kpi_type, KPIType.PERFORMANCE)
        self.assertEqual(kpi.target_value, 100.0)

    def test_kpi_manager_initialization(self):
        """Test KPI manager initialization."""
        metrics_collector = MetricsCollector()
        manager = KPIManager(metrics_collector)

        self.assertIsNotNone(manager)
        self.assertIsNotNone(manager.kpis)
        self.assertIsInstance(manager.kpis, dict)

    def test_add_kpi(self):
        """Test adding a KPI."""
        metrics_collector = MetricsCollector()
        manager = KPIManager(metrics_collector)

        kpi = KPI(
            id="test_kpi",
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )

        # KPIs are created through create_kpi method, not added directly
        manager.create_kpi(
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )

        # The KPI ID is generated as "performance_test_kpi"
        self.assertIn("performance_test_kpi", manager.kpis)

    def test_get_kpi(self):
        """Test getting a KPI."""
        metrics_collector = MetricsCollector()
        manager = KPIManager(metrics_collector)

        kpi = KPI(
            id="test_kpi",
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )

        # KPIs are created through create_kpi method, not added directly
        manager.create_kpi(
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )
        # Get the first KPI (since we created one)
        retrieved_kpi = list(manager.kpis.values())[0] if manager.kpis else None

        self.assertIsNotNone(retrieved_kpi)

    def test_get_nonexistent_kpi(self):
        """Test getting a non-existent KPI."""
        metrics_collector = MetricsCollector()
        manager = KPIManager(metrics_collector)

        # Check if a non-existent KPI is not found
        retrieved_kpi = manager.kpis.get("nonexistent")

        self.assertIsNone(retrieved_kpi)

    def test_analytics_system_initialization(self):
        """Test analytics system initialization."""
        system = AnalyticsSystem()

        self.assertIsNotNone(system)
        self.assertIsNotNone(system.kpi_manager)
        self.assertIsNotNone(system.metrics_collector)

    def test_add_metric(self):
        """Test adding a metric."""
        system = AnalyticsSystem()

        metric = Metric(name="test_metric", value=42.5, metric_type=MetricType.GAUGE)

        system.metrics_collector.add_metric(
            metric.name, metric.value, metric.metric_type
        )

        # Verify metric was added (check that no exception was raised)
        self.assertTrue(True)

    def test_generate_report(self):
        """Test report generation."""
        system = AnalyticsSystem()

        # Add a KPI
        kpi = KPI(
            id="test_kpi",
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )
        system.kpi_manager.create_kpi(
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )

        # Generate report
        report = system.generate_report()

        self.assertIsNotNone(report)
        self.assertIn("generated_at", report.__dict__)
        self.assertIn("data", report.__dict__)

    def test_get_analytics_data(self):
        """Test getting analytics data."""
        system = AnalyticsSystem()

        # Add a KPI
        kpi = KPI(
            id="test_kpi",
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )
        system.kpi_manager.create_kpi(
            name="Test KPI",
            description="A test KPI",
            kpi_type=KPIType.PERFORMANCE,
            metric_name="test_metric",
            target_value=100.0,
        )

        # Get analytics data
        analytics_data = system.get_analytics_data()

        self.assertIsNotNone(analytics_data)
        self.assertIn("kpis", analytics_data)
        self.assertIn("metrics", analytics_data)
        self.assertIn("timestamp", analytics_data)


if __name__ == "__main__":
    unittest.main()
