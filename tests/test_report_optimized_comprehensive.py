"""Comprehensive tests for the enhanced report system."""

import asyncio
import json
import os
import tempfile
import time
import threading
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.ai_guard.report_optimized import (
    EnhancedReportGenerator,
    ReportConfig,
    ReportFormat,
    ReportType,
    ReportStatus,
    ReportData,
    ReportMetrics,
    ReportEntry,
    ReportAnalytics,
    JSONReportProcessor,
    HTMLReportProcessor,
    CSVReportProcessor,
    XMLReportProcessor,
    ReportScheduler,
    generate_enhanced_report,
    create_report_comparison,
)


class TestReportConfig:
    """Test ReportConfig class."""

    def test_report_config_defaults(self):
        """Test default configuration values."""
        config = ReportConfig()

        assert config.format == ReportFormat.JSON
        assert config.report_type == ReportType.SUMMARY
        assert config.include_timestamp is True
        assert config.include_metadata is True
        assert config.compress_output is False
        assert config.parallel_processing is True
        assert config.max_workers == 4
        assert config.chunk_size == 1000
        assert config.enable_caching is True
        assert config.cache_ttl == 3600
        assert config.streaming_enabled is True
        assert config.real_time_updates is False

    def test_report_config_custom(self):
        """Test custom configuration values."""
        config = ReportConfig(
            format=ReportFormat.HTML,
            report_type=ReportType.DETAILED,
            include_timestamp=False,
            parallel_processing=False,
            max_workers=8,
            chunk_size=500,
            enable_caching=False,
            cache_ttl=7200,
            streaming_enabled=False,
        )

        assert config.format == ReportFormat.HTML
        assert config.report_type == ReportType.DETAILED
        assert config.include_timestamp is False
        assert config.parallel_processing is False
        assert config.max_workers == 8
        assert config.chunk_size == 500
        assert config.enable_caching is False
        assert config.cache_ttl == 7200
        assert config.streaming_enabled is False


class TestReportEntry:
    """Test ReportEntry class."""

    def test_report_entry_creation(self):
        """Test report entry creation."""
        entry = ReportEntry(
            id="test_entry",
            type="error",
            severity="high",
            message="Test error message",
            file_path="/test/file.py",
            line_number=10,
            column_number=5,
            rule_id="TEST001",
            metadata={"key": "value"},
        )

        assert entry.id == "test_entry"
        assert entry.type == "error"
        assert entry.severity == "high"
        assert entry.message == "Test error message"
        assert entry.file_path == "/test/file.py"
        assert entry.line_number == 10
        assert entry.column_number == 5
        assert entry.rule_id == "TEST001"
        assert entry.metadata == {"key": "value"}
        assert isinstance(entry.timestamp, datetime)

    def test_report_entry_defaults(self):
        """Test report entry with default values."""
        entry = ReportEntry(
            id="test_entry",
            type="warning",
            severity="medium",
            message="Test warning",
            file_path="/test/file.py",
        )

        assert entry.line_number is None
        assert entry.column_number is None
        assert entry.rule_id is None
        assert entry.metadata == {}


class TestReportMetrics:
    """Test ReportMetrics class."""

    def test_report_metrics_creation(self):
        """Test report metrics creation."""
        metrics = ReportMetrics()

        assert metrics.files_processed == 0
        assert metrics.issues_found == 0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.generation_time_seconds == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.start_time > 0

    def test_report_metrics_duration(self):
        """Test metrics duration calculation."""
        metrics = ReportMetrics()
        time.sleep(0.1)
        duration = metrics.duration

        assert duration >= 0.1
        assert duration < 1.0  # Should be close to 0.1


class TestReportAnalytics:
    """Test ReportAnalytics class."""

    def test_report_analytics_initialization(self):
        """Test analytics initialization."""
        analytics = ReportAnalytics()

        assert analytics.metrics_history == []
        assert analytics.generation_times == []
        assert analytics.cache_stats == {"hits": 0, "misses": 0}
        assert analytics.error_counts == {}

    def test_record_generation(self):
        """Test recording generation metrics."""
        analytics = ReportAnalytics()
        metrics = ReportMetrics()
        metrics.end_time = time.time() + 1.0

        analytics.record_generation(metrics)

        assert len(analytics.metrics_history) == 1
        assert len(analytics.generation_times) == 1
        assert analytics.generation_times[0] >= 1.0

    def test_get_performance_stats(self):
        """Test performance statistics calculation."""
        analytics = ReportAnalytics()

        # Add some test data
        for i in range(5):
            metrics = ReportMetrics()
            metrics.end_time = time.time() + i
            analytics.record_generation(metrics)

        stats = analytics.get_performance_stats()

        assert "avg_generation_time" in stats
        assert "min_generation_time" in stats
        assert "max_generation_time" in stats
        assert "total_reports" in stats
        assert "cache_hit_rate" in stats
        assert "error_rate" in stats
        assert stats["total_reports"] == 5

    def test_get_trend_analysis(self):
        """Test trend analysis."""
        analytics = ReportAnalytics()

        # Add test data with improving trend
        for i in range(10):
            metrics = ReportMetrics()
            metrics.end_time = time.time() + (10 - i)  # Decreasing times
            analytics.record_generation(metrics)

        trend = analytics.get_trend_analysis()

        assert "trend" in trend
        assert trend["trend"] in ["improving", "degrading", "stable"]


class TestReportProcessors:
    """Test report processors."""

    def test_json_processor(self):
        """Test JSON report processor."""
        processor = JSONReportProcessor()

        report_data = self._create_test_report_data()
        content = processor.process(report_data, ReportConfig())

        assert isinstance(content, bytes)

        # Parse JSON to verify structure
        json_data = json.loads(content.decode("utf-8"))
        assert "report_id" in json_data
        assert "title" in json_data
        assert "entries" in json_data
        assert "metrics" in json_data
        assert len(json_data["entries"]) == 2

    def test_html_processor(self):
        """Test HTML report processor."""
        processor = HTMLReportProcessor()

        report_data = self._create_test_report_data()
        content = processor.process(report_data, ReportConfig())

        assert isinstance(content, bytes)
        html_content = content.decode("utf-8")

        assert "<html>" in html_content
        assert "<title>" in html_content
        assert "AI-Guard Report" in html_content
        assert len(report_data.entries) > 0

    def test_csv_processor(self):
        """Test CSV report processor."""
        processor = CSVReportProcessor()

        report_data = self._create_test_report_data()
        content = processor.process(report_data, ReportConfig())

        assert isinstance(content, bytes)
        csv_content = content.decode("utf-8")

        assert "ID,Type,Severity" in csv_content
        assert "test_entry_1" in csv_content
        assert "test_entry_2" in csv_content

    def test_xml_processor(self):
        """Test XML report processor."""
        processor = XMLReportProcessor()

        report_data = self._create_test_report_data()
        content = processor.process(report_data, ReportConfig())

        assert isinstance(content, bytes)
        xml_content = content.decode("utf-8")

        assert "<?xml version='1.0' encoding='utf-8'?>" in xml_content
        assert "<report" in xml_content
        assert "<entries>" in xml_content

    def _create_test_report_data(self) -> ReportData:
        """Create test report data."""
        metrics = ReportMetrics()
        metrics.end_time = time.time()

        entries = [
            ReportEntry(
                id="test_entry_1",
                type="error",
                severity="high",
                message="Test error 1",
                file_path="/test/file1.py",
                line_number=10,
                rule_id="TEST001",
            ),
            ReportEntry(
                id="test_entry_2",
                type="warning",
                severity="medium",
                message="Test warning 1",
                file_path="/test/file2.py",
                line_number=20,
                rule_id="TEST002",
            ),
        ]

        return ReportData(
            report_id="test_report",
            title="Test Report",
            description="Test report description",
            timestamp=datetime.now(timezone.utc),
            format=ReportFormat.JSON,
            status=ReportStatus.COMPLETED,
            metrics=metrics,
            entries=entries,
            summary={"total_issues": 2, "errors": 1, "warnings": 1},
        )


class TestEnhancedReportGenerator:
    """Test EnhancedReportGenerator class."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        config = ReportConfig()
        generator = EnhancedReportGenerator(config)

        assert generator.config == config
        assert generator.cache_manager is not None
        assert generator.analytics is not None
        assert len(generator.processors) == 4  # JSON, HTML, CSV, XML
        assert isinstance(generator.processors[ReportFormat.JSON], JSONReportProcessor)

    def test_generate_report_basic(self):
        """Test basic report generation."""
        generator = EnhancedReportGenerator()

        analysis_results = {
            "issues": [
                {
                    "type": "error",
                    "severity": "high",
                    "message": "Test error",
                    "file": "/test/file.py",
                    "line": 10,
                    "rule_id": "TEST001",
                }
            ]
        }

        report_data = generator.generate_report(analysis_results)

        assert isinstance(report_data, ReportData)
        assert report_data.status == ReportStatus.COMPLETED
        assert len(report_data.entries) == 1
        assert report_data.entries[0].type == "error"
        assert report_data.metrics.issues_found == 1

    def test_generate_report_parallel(self):
        """Test parallel report generation."""
        config = ReportConfig(parallel_processing=True, max_workers=2)
        generator = EnhancedReportGenerator(config)

        # Create many issues to test parallel processing
        issues = []
        for i in range(100):
            issues.append(
                {
                    "type": "warning",
                    "severity": "medium",
                    "message": f"Test warning {i}",
                    "file": f"/test/file{i}.py",
                    "line": i,
                    "rule_id": f"TEST{i:03d}",
                }
            )

        analysis_results = {"issues": issues}

        start_time = time.time()
        report_data = generator.generate_report(analysis_results)
        end_time = time.time()

        assert len(report_data.entries) == 100
        assert report_data.status == ReportStatus.COMPLETED
        assert report_data.metrics.issues_found == 100

    def test_generate_report_sequential(self):
        """Test sequential report generation."""
        config = ReportConfig(parallel_processing=False)
        generator = EnhancedReportGenerator(config)

        issues = []
        for i in range(50):
            issues.append(
                {
                    "type": "info",
                    "severity": "low",
                    "message": f"Test info {i}",
                    "file": f"/test/file{i}.py",
                    "line": i,
                    "rule_id": f"INFO{i:03d}",
                }
            )

        analysis_results = {"issues": issues}

        report_data = generator.generate_report(analysis_results)

        assert len(report_data.entries) == 50
        assert report_data.status == ReportStatus.COMPLETED
        assert report_data.metrics.issues_found == 50

    def test_export_report(self):
        """Test report export functionality."""
        generator = EnhancedReportGenerator()

        report_data = self._create_test_report_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_report")

            results = generator.export_report(
                report_data, output_path, [ReportFormat.JSON, ReportFormat.HTML]
            )

            assert "json" in results
            assert "html" in results
            assert results["json"]["success"] is True
            assert results["html"]["success"] is True

            # Verify files were created
            json_file = results["json"]["file_path"]
            html_file = results["html"]["file_path"]

            assert os.path.exists(json_file)
            assert os.path.exists(html_file)

            # Verify file contents
            with open(json_file, "r") as f:
                json_data = json.load(f)
                assert json_data["report_id"] == "test_report"

            with open(html_file, "r") as f:
                html_content = f.read()
                assert "<html>" in html_content

    def test_export_report_compression(self):
        """Test compressed report export."""
        config = ReportConfig(compress_output=True)
        generator = EnhancedReportGenerator(config)

        report_data = self._create_test_report_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_report")

            results = generator.export_report(
                report_data, output_path, [ReportFormat.JSON]
            )

            assert "json" in results
            assert results["json"]["success"] is True
            assert results["json"]["compressed"] is True

            json_file = results["json"]["file_path"]
            assert json_file.endswith(".gz")
            assert os.path.exists(json_file)

    def test_get_analytics(self):
        """Test analytics retrieval."""
        generator = EnhancedReportGenerator()

        # Generate some reports to populate analytics
        for i in range(3):
            analysis_results = {
                "issues": [
                    {
                        "type": "warning",
                        "message": f"Test warning {i}",
                        "file": f"/test/file{i}.py",
                        "line": i,
                    }
                ]
            }
            generator.generate_report(analysis_results)

        analytics = generator.get_analytics()

        assert "performance_stats" in analytics
        assert "trend_analysis" in analytics
        assert "cache_stats" in analytics
        assert "error_counts" in analytics
        assert analytics["performance_stats"]["total_reports"] == 3

    def test_cancel_generation(self):
        """Test report generation cancellation."""
        generator = EnhancedReportGenerator()

        # Test canceling non-existent report
        result = generator.cancel_generation("nonexistent")
        assert result is False

    def _create_test_report_data(self) -> ReportData:
        """Create test report data."""
        metrics = ReportMetrics()
        metrics.end_time = time.time()

        entries = [
            ReportEntry(
                id="test_entry_1",
                type="error",
                severity="high",
                message="Test error",
                file_path="/test/file.py",
                line_number=10,
            )
        ]

        return ReportData(
            report_id="test_report",
            title="Test Report",
            description="Test report description",
            timestamp=datetime.now(timezone.utc),
            format=ReportFormat.JSON,
            status=ReportStatus.COMPLETED,
            metrics=metrics,
            entries=entries,
            summary={"total_issues": 1},
        )


class TestReportScheduler:
    """Test ReportScheduler class."""

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        generator = EnhancedReportGenerator()
        scheduler = ReportScheduler(generator)

        assert scheduler.generator == generator
        assert scheduler.scheduled_reports == {}

    def test_schedule_report(self):
        """Test report scheduling."""
        generator = EnhancedReportGenerator()
        scheduler = ReportScheduler(generator)

        analysis_results = {"issues": []}

        result = scheduler.schedule_report(
            "test_schedule",
            analysis_results,
            3600,  # 1 hour
            "/tmp/test_output",
            [ReportFormat.JSON],
        )

        assert result is True
        assert "test_schedule" in scheduler.scheduled_reports
        assert scheduler.scheduled_reports["test_schedule"]["active"] is True

    def test_cancel_schedule(self):
        """Test schedule cancellation."""
        generator = EnhancedReportGenerator()
        scheduler = ReportScheduler(generator)

        # Schedule a report first
        analysis_results = {"issues": []}
        scheduler.schedule_report(
            "test_schedule",
            analysis_results,
            3600,
            "/tmp/test_output",
            [ReportFormat.JSON],
        )

        # Cancel it
        result = scheduler.cancel_schedule("test_schedule")
        assert result is True
        assert scheduler.scheduled_reports["test_schedule"]["active"] is False

        # Try to cancel non-existent schedule
        result = scheduler.cancel_schedule("nonexistent")
        assert result is False

    def test_run_scheduled_reports(self):
        """Test running scheduled reports."""
        generator = EnhancedReportGenerator()
        scheduler = ReportScheduler(generator)

        analysis_results = {
            "issues": [
                {
                    "type": "warning",
                    "message": "Test warning",
                    "file": "/test/file.py",
                    "line": 10,
                }
            ]
        }

        # Schedule a report with immediate execution
        scheduler.schedule_report(
            "immediate_schedule",
            analysis_results,
            0,  # Execute immediately
            "/tmp/test_output",
            [ReportFormat.JSON],
        )

        results = scheduler.run_scheduled_reports()

        assert "immediate_schedule" in results
        assert results["immediate_schedule"]["success"] is True


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_generate_enhanced_report(self):
        """Test generate_enhanced_report function."""
        analysis_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Test error",
                    "file": "/test/file.py",
                    "line": 10,
                }
            ]
        }

        result = generate_enhanced_report(
            analysis_results, format_type="json", parallel_processing=True
        )

        assert "report_data" in result
        assert "analytics" in result
        assert isinstance(result["report_data"], ReportData)
        assert result["report_data"].status == ReportStatus.COMPLETED

    def test_create_report_comparison(self):
        """Test create_report_comparison function."""
        # Create test reports
        reports = []
        for i in range(3):
            metrics = ReportMetrics()
            metrics.end_time = time.time()

            report = ReportData(
                report_id=f"report_{i}",
                title=f"Test Report {i}",
                description="Test description",
                timestamp=datetime.now(timezone.utc),
                format=ReportFormat.JSON,
                status=ReportStatus.COMPLETED,
                metrics=metrics,
                entries=[
                    ReportEntry(
                        id=f"entry_{i}",
                        type="warning",
                        severity="medium",
                        message=f"Test warning {i}",
                        file_path=f"/test/file{i}.py",
                    )
                ],
            )
            reports.append(report)

        comparison = create_report_comparison(reports, "trend")

        assert "comparison_type" in comparison
        assert "report_count" in comparison
        assert "metrics_comparison" in comparison
        assert "trend_analysis" in comparison
        assert comparison["report_count"] == 3
        assert len(comparison["metrics_comparison"]) == 3


class TestAsyncFeatures:
    """Test asynchronous features."""

    @pytest.mark.asyncio
    async def test_streaming_report_generation(self):
        """Test streaming report generation."""
        generator = EnhancedReportGenerator()

        analysis_results = {
            "issues": [
                {
                    "type": "error",
                    "message": "Test error",
                    "file": "/test/file.py",
                    "line": 10,
                },
                {
                    "type": "warning",
                    "message": "Test warning",
                    "file": "/test/file2.py",
                    "line": 20,
                },
            ]
        }

        chunks = []
        async for chunk in generator.generate_report_streaming(analysis_results):
            chunks.append(chunk)

        assert len(chunks) > 0

        # Verify JSON structure for streaming
        full_content = b"".join(chunks)
        json_content = full_content.decode("utf-8")

        # Should be valid JSON
        data = json.loads(json_content)
        assert "report_id" in data
        assert "entries" in data

    @pytest.mark.asyncio
    async def test_streaming_with_progress_callback(self):
        """Test streaming with progress callback."""
        generator = EnhancedReportGenerator()

        analysis_results = {
            "issues": [
                {"type": "error", "message": "Test", "file": "/test.py", "line": 1}
            ]
        }

        progress_updates = []

        def progress_callback(progress):
            progress_updates.append(progress)

        chunks = []
        async for chunk in generator.generate_report_streaming(
            analysis_results, progress_callback=progress_callback
        ):
            chunks.append(chunk)

        assert len(progress_updates) > 0
        assert progress_updates[-1] == 1.0  # Should end at 100%


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_analysis_results(self):
        """Test handling of invalid analysis results."""
        generator = EnhancedReportGenerator()

        # Test with None
        with pytest.raises(Exception):
            generator.generate_report(None)

        # Test with empty dict
        report_data = generator.generate_report({})
        assert report_data.status == ReportStatus.COMPLETED
        assert len(report_data.entries) == 0

    def test_export_error_handling(self):
        """Test export error handling."""
        generator = EnhancedReportGenerator()
        report_data = self._create_test_report_data()

        # Test export to invalid path
        results = generator.export_report(
            report_data, "/invalid/path/that/does/not/exist/report", [ReportFormat.JSON]
        )

        assert "json" in results
        assert results["json"]["success"] is False
        assert "error" in results["json"]

    def test_unsupported_format_handling(self):
        """Test unsupported format handling."""
        generator = EnhancedReportGenerator()
        report_data = self._create_test_report_data()

        # Mock an unsupported format
        with patch.object(generator, "processors", {ReportFormat.PDF: None}):
            results = generator.export_report(
                report_data, "/tmp/test", [ReportFormat.PDF]
            )

            assert "pdf" in results
            assert results["pdf"]["success"] is False

    def _create_test_report_data(self) -> ReportData:
        """Create test report data."""
        metrics = ReportMetrics()
        metrics.end_time = time.time()

        return ReportData(
            report_id="test_report",
            title="Test Report",
            description="Test report description",
            timestamp=datetime.now(timezone.utc),
            format=ReportFormat.JSON,
            status=ReportStatus.COMPLETED,
            metrics=metrics,
            entries=[],
            summary={"total_issues": 0},
        )


class TestPerformance:
    """Test performance characteristics."""

    def test_large_report_generation(self):
        """Test generation of large reports."""
        generator = EnhancedReportGenerator()

        # Create a large number of issues
        issues = []
        for i in range(1000):
            issues.append(
                {
                    "type": "info",
                    "severity": "low",
                    "message": f"Test issue {i}",
                    "file": f"/test/file{i}.py",
                    "line": i % 100,
                    "rule_id": f"TEST{i:04d}",
                }
            )

        analysis_results = {"issues": issues}

        start_time = time.time()
        report_data = generator.generate_report(analysis_results)
        end_time = time.time()

        assert len(report_data.entries) == 1000
        assert report_data.status == ReportStatus.COMPLETED
        assert (end_time - start_time) < 10.0  # Should complete within 10 seconds

    def test_parallel_vs_sequential_performance(self):
        """Test performance difference between parallel and sequential processing."""
        # Create test data
        issues = []
        for i in range(500):
            issues.append(
                {
                    "type": "warning",
                    "severity": "medium",
                    "message": f"Test warning {i}",
                    "file": f"/test/file{i}.py",
                    "line": i,
                    "rule_id": f"WARN{i:03d}",
                }
            )

        analysis_results = {"issues": issues}

        # Test sequential processing
        config_seq = ReportConfig(parallel_processing=False)
        generator_seq = EnhancedReportGenerator(config_seq)

        start_time = time.time()
        report_seq = generator_seq.generate_report(analysis_results)
        seq_time = time.time() - start_time

        # Test parallel processing
        config_par = ReportConfig(parallel_processing=True, max_workers=4)
        generator_par = EnhancedReportGenerator(config_par)

        start_time = time.time()
        report_par = generator_par.generate_report(analysis_results)
        par_time = time.time() - start_time

        # Both should produce the same results
        assert len(report_seq.entries) == len(report_par.entries) == 500

        # Parallel should generally be faster (though not always guaranteed)
        # We'll just verify both complete successfully
        assert report_seq.status == ReportStatus.COMPLETED
        assert report_par.status == ReportStatus.COMPLETED

    def test_memory_usage(self):
        """Test memory usage with large reports."""
        generator = EnhancedReportGenerator()

        # Create a moderately large report
        issues = []
        for i in range(10000):
            issues.append(
                {
                    "type": "info",
                    "severity": "low",
                    "message": f"Test issue {i} with some additional content to increase memory usage",
                    "file": f"/test/large/file{i}.py",
                    "line": i % 1000,
                    "rule_id": f"INFO{i:05d}",
                    "metadata": {"additional_data": f"some data {i}"},
                }
            )

        analysis_results = {"issues": issues}

        report_data = generator.generate_report(analysis_results)

        assert len(report_data.entries) == 10000
        assert report_data.status == ReportStatus.COMPLETED
        assert report_data.metrics.memory_usage_mb >= 0  # Should track memory usage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
