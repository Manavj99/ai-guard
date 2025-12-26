"""Enhanced reporting system with streaming, parallel processing, and analytics for AI-Guard."""

import asyncio
import json
import logging
import os
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Protocol,
    runtime_checkable,
)
import gzip
import csv
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO

from .cache import CacheManager, CacheConfig
from .config import Config


logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats."""

    JSON = "json"
    HTML = "html"
    SARIF = "sarif"
    XML = "xml"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "xlsx"


class ReportType(Enum):
    """Report types."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    COMPARATIVE = "comparative"
    TREND = "trend"
    DASHBOARD = "dashboard"


class ReportStatus(Enum):
    """Report generation status."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ReportMetrics:
    """Report generation metrics."""

    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    files_processed: int = 0
    issues_found: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    generation_time_seconds: float = 0.0
    compression_ratio: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def duration(self) -> float:
        """Get generation duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time


@dataclass
class ReportConfig:
    """Report generation configuration."""

    format: ReportFormat = ReportFormat.JSON
    report_type: ReportType = ReportType.SUMMARY
    include_timestamp: bool = True
    include_metadata: bool = True
    compress_output: bool = False
    parallel_processing: bool = True
    max_workers: int = 4
    chunk_size: int = 1000
    enable_caching: bool = True
    cache_ttl: int = 3600
    template_path: Optional[str] = None
    custom_styles: Optional[Dict[str, Any]] = None
    export_formats: List[ReportFormat] = field(default_factory=list)
    streaming_enabled: bool = True
    real_time_updates: bool = False


@dataclass
class ReportEntry:
    """Individual report entry."""

    id: str
    type: str
    severity: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    rule_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportData:
    """Complete report data structure."""

    report_id: str
    title: str
    description: str
    timestamp: datetime
    format: ReportFormat
    status: ReportStatus
    metrics: ReportMetrics
    entries: List[ReportEntry] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ReportProcessor(Protocol):
    """Protocol for report processors."""

    def process(self, data: ReportData, config: ReportConfig) -> bytes:
        """Process report data and return bytes."""
        ...


class ReportAnalytics:
    """Report analytics and performance monitoring."""

    def __init__(self):
        self.metrics_history: List[ReportMetrics] = []
        self.generation_times: List[float] = []
        self.cache_stats: Dict[str, int] = {"hits": 0, "misses": 0}
        self.error_counts: Dict[str, int] = {}

    def record_generation(self, metrics: ReportMetrics) -> None:
        """Record report generation metrics."""
        self.metrics_history.append(metrics)
        self.generation_times.append(metrics.duration)

        # Keep only last 1000 entries
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
            self.generation_times = self.generation_times[-1000:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.generation_times:
            return {}

        return {
            "avg_generation_time": sum(self.generation_times)
            / len(self.generation_times),
            "min_generation_time": min(self.generation_times),
            "max_generation_time": max(self.generation_times),
            "total_reports": len(self.generation_times),
            "cache_hit_rate": (
                self.cache_stats["hits"]
                / (self.cache_stats["hits"] + self.cache_stats["misses"])
                if (self.cache_stats["hits"] + self.cache_stats["misses"]) > 0
                else 0
            ),
            "error_rate": (
                sum(self.error_counts.values()) / len(self.generation_times)
                if self.generation_times
                else 0
            ),
        }

    def get_trend_analysis(self) -> Dict[str, Any]:
        """Get trend analysis of report generation."""
        if len(self.generation_times) < 2:
            return {"trend": "insufficient_data"}

        # Simple linear trend analysis
        recent_avg = sum(self.generation_times[-10:]) / min(
            10, len(self.generation_times)
        )
        older_avg = sum(self.generation_times[:-10]) / max(
            1, len(self.generation_times) - 10
        )

        if recent_avg > older_avg * 1.1:
            trend = "degrading"
        elif recent_avg < older_avg * 0.9:
            trend = "improving"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "recent_avg": recent_avg,
            "older_avg": older_avg,
            "change_percent": (
                ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
            ),
        }


class JSONReportProcessor:
    """JSON report processor."""

    def process(self, data: ReportData, config: ReportConfig) -> bytes:
        """Process report data into JSON format."""
        report_dict = {
            "report_id": data.report_id,
            "title": data.title,
            "description": data.description,
            "timestamp": data.timestamp.isoformat(),
            "format": data.format.value,
            "status": data.status.value,
            "metrics": {
                "generation_time": data.metrics.duration,
                "files_processed": data.metrics.files_processed,
                "issues_found": data.metrics.issues_found,
                "memory_usage_mb": data.metrics.memory_usage_mb,
                "compression_ratio": data.metrics.compression_ratio,
            },
            "summary": data.summary,
            "entries": [
                {
                    "id": entry.id,
                    "type": entry.type,
                    "severity": entry.severity,
                    "message": entry.message,
                    "file_path": entry.file_path,
                    "line_number": entry.line_number,
                    "column_number": entry.column_number,
                    "rule_id": entry.rule_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "metadata": entry.metadata,
                }
                for entry in data.entries
            ],
            "metadata": data.metadata,
        }

        json_str = json.dumps(report_dict, indent=2, ensure_ascii=False)
        return json_str.encode("utf-8")


class HTMLReportProcessor:
    """HTML report processor with advanced templates."""

    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or self._get_default_template_dir()

    def _get_default_template_dir(self) -> str:
        """Get default template directory."""
        return os.path.join(os.path.dirname(__file__), "templates")

    def process(self, data: ReportData, config: ReportConfig) -> bytes:
        """Process report data into HTML format."""
        html_content = self._generate_html(data, config)
        return html_content.encode("utf-8")

    def _generate_html(self, data: ReportData, config: ReportConfig) -> str:
        """Generate HTML content."""
        css_styles = self._get_css_styles()
        js_scripts = self._get_js_scripts()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.title}</title>
    <style>{css_styles}</style>
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>{data.title}</h1>
            <p class="report-description">{data.description}</p>
            <div class="report-meta">
                <span class="timestamp">Generated: {data.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
                <span class="report-id">ID: {data.report_id}</span>
            </div>
        </header>
        
        <section class="summary-section">
            {self._generate_summary_html(data)}
        </section>
        
        <section class="metrics-section">
            {self._generate_metrics_html(data)}
        </section>
        
        <section class="entries-section">
            {self._generate_entries_html(data)}
        </section>
        
        <footer class="report-footer">
            <p>Generated by AI-Guard Enhanced Report System</p>
        </footer>
    </div>
    
    <script>{js_scripts}</script>
</body>
</html>"""

        return html

    def _get_css_styles(self) -> str:
        """Get CSS styles."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .report-header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .report-description {
            margin: 0 0 15px 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .report-meta {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .summary-section, .metrics-section, .entries-section {
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #667eea;
        }
        
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .metric-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric-label {
            font-weight: 500;
            color: #666;
        }
        
        .metric-value {
            font-weight: bold;
            color: #333;
        }
        
        .entries-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .entries-table th,
        .entries-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        .entries-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        .severity-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .severity-error {
            background-color: #fee;
            color: #c53030;
        }
        
        .severity-warning {
            background-color: #fffbeb;
            color: #d69e2e;
        }
        
        .severity-info {
            background-color: #ebf8ff;
            color: #3182ce;
        }
        
        .file-path {
            font-family: monospace;
            background-color: #f1f5f9;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        
        .report-footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .report-header h1 {
                font-size: 2em;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .entries-table {
                font-size: 0.9em;
            }
        }
        """

    def _get_js_scripts(self) -> str:
        """Get JavaScript for interactive features."""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            // Add search functionality
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.placeholder = 'Search entries...';
            searchInput.style.cssText = 'width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px;';
            
            const entriesSection = document.querySelector('.entries-section');
            const table = document.querySelector('.entries-table');
            
            if (table && entriesSection) {
                entriesSection.insertBefore(searchInput, table);
                
                searchInput.addEventListener('input', function() {
                    const searchTerm = this.value.toLowerCase();
                    const rows = table.querySelectorAll('tbody tr');
                    
                    rows.forEach(row => {
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(searchTerm) ? '' : 'none';
                    });
                });
            }
            
            // Add export functionality
            const exportBtn = document.createElement('button');
            exportBtn.textContent = 'Export as JSON';
            exportBtn.style.cssText = 'background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 10px 0;';
            
            exportBtn.addEventListener('click', function() {
                const reportData = {
                    title: document.querySelector('h1').textContent,
                    timestamp: document.querySelector('.timestamp').textContent,
                    entries: Array.from(table.querySelectorAll('tbody tr')).map(row => {
                        const cells = row.querySelectorAll('td');
                        return {
                            type: cells[0]?.textContent,
                            severity: cells[1]?.textContent,
                            file: cells[2]?.textContent,
                            line: cells[3]?.textContent,
                            message: cells[4]?.textContent
                        };
                    })
                };
                
                const blob = new Blob([JSON.stringify(reportData, null, 2)], {type: 'application/json'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'ai-guard-report.json';
                a.click();
                URL.revokeObjectURL(url);
            });
            
            if (entriesSection) {
                entriesSection.appendChild(exportBtn);
            }
        });
        """

    def _generate_summary_html(self, data: ReportData) -> str:
        """Generate summary section HTML."""
        summary = data.summary
        total_entries = len(data.entries)
        error_count = len([e for e in data.entries if e.severity == "error"])
        warning_count = len([e for e in data.entries if e.severity == "warning"])
        info_count = len([e for e in data.entries if e.severity == "info"])

        return f"""
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Issues</h3>
                <div class="value">{total_entries}</div>
            </div>
            <div class="summary-card">
                <h3>Errors</h3>
                <div class="value" style="color: #c53030;">{error_count}</div>
            </div>
            <div class="summary-card">
                <h3>Warnings</h3>
                <div class="value" style="color: #d69e2e;">{warning_count}</div>
            </div>
            <div class="summary-card">
                <h3>Info</h3>
                <div class="value" style="color: #3182ce;">{info_count}</div>
            </div>
        </div>
        """

    def _generate_metrics_html(self, data: ReportData) -> str:
        """Generate metrics section HTML."""
        metrics = data.metrics

        return f"""
        <h2>Generation Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-item">
                <span class="metric-label">Generation Time</span>
                <span class="metric-value">{metrics.duration:.2f}s</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Files Processed</span>
                <span class="metric-value">{metrics.files_processed}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Memory Usage</span>
                <span class="metric-value">{metrics.memory_usage_mb:.1f} MB</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Cache Hit Rate</span>
                <span class="metric-value">{(metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100) if (metrics.cache_hits + metrics.cache_misses) > 0 else 0:.1f}%</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Compression Ratio</span>
                <span class="metric-value">{metrics.compression_ratio:.1f}%</span>
            </div>
        </div>
        """

    def _generate_entries_html(self, data: ReportData) -> str:
        """Generate entries section HTML."""
        if not data.entries:
            return "<h2>Issues</h2><p>No issues found.</p>"

        rows_html = ""
        for entry in data.entries:
            severity_class = f"severity-{entry.severity}"
            line_info = f":{entry.line_number}" if entry.line_number else ""

            rows_html += f"""
            <tr>
                <td>{entry.type}</td>
                <td><span class="severity-badge {severity_class}">{entry.severity}</span></td>
                <td><span class="file-path">{entry.file_path}{line_info}</span></td>
                <td>{entry.line_number or '-'}</td>
                <td>{entry.message}</td>
            </tr>
            """

        return f"""
        <h2>Issues ({len(data.entries)})</h2>
        <table class="entries-table">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>File</th>
                    <th>Line</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """


class CSVReportProcessor:
    """CSV report processor."""

    def process(self, data: ReportData, config: ReportConfig) -> bytes:
        """Process report data into CSV format."""
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "ID",
                "Type",
                "Severity",
                "Message",
                "File Path",
                "Line Number",
                "Column Number",
                "Rule ID",
                "Timestamp",
            ]
        )

        # Write entries
        for entry in data.entries:
            writer.writerow(
                [
                    entry.id,
                    entry.type,
                    entry.severity,
                    entry.message,
                    entry.file_path,
                    entry.line_number or "",
                    entry.column_number or "",
                    entry.rule_id or "",
                    entry.timestamp.isoformat(),
                ]
            )

        return output.getvalue().encode("utf-8")


class XMLReportProcessor:
    """XML report processor."""

    def process(self, data: ReportData, config: ReportConfig) -> bytes:
        """Process report data into XML format."""
        root = ET.Element("report")
        root.set("id", data.report_id)
        root.set("title", data.title)
        root.set("timestamp", data.timestamp.isoformat())

        # Add metadata
        metadata = ET.SubElement(root, "metadata")
        metadata.set("format", data.format.value)
        metadata.set("status", data.status.value)

        # Add metrics
        metrics = ET.SubElement(root, "metrics")
        metrics.set("generation_time", str(data.metrics.duration))
        metrics.set("files_processed", str(data.metrics.files_processed))
        metrics.set("issues_found", str(data.metrics.issues_found))

        # Add entries
        entries = ET.SubElement(root, "entries")
        for entry in data.entries:
            entry_elem = ET.SubElement(entries, "entry")
            entry_elem.set("id", entry.id)
            entry_elem.set("type", entry.type)
            entry_elem.set("severity", entry.severity)
            entry_elem.set("file_path", entry.file_path)
            if entry.line_number:
                entry_elem.set("line_number", str(entry.line_number))
            if entry.column_number:
                entry_elem.set("column_number", str(entry.column_number))
            if entry.rule_id:
                entry_elem.set("rule_id", entry.rule_id)

            message_elem = ET.SubElement(entry_elem, "message")
            message_elem.text = entry.message

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)


class EnhancedReportGenerator:
    """Enhanced report generator with streaming, parallel processing, and analytics."""

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.cache_manager = CacheManager(
            CacheConfig(
                strategy="lru",
                max_size=1000,
                ttl=self.config.cache_ttl,
                enable_compression=True,
            )
        )
        self.analytics = ReportAnalytics()
        self.processors: Dict[ReportFormat, ReportProcessor] = {
            ReportFormat.JSON: JSONReportProcessor(),
            ReportFormat.HTML: HTMLReportProcessor(),
            ReportFormat.CSV: CSVReportProcessor(),
            ReportFormat.XML: XMLReportProcessor(),
        }
        self._active_generations: Dict[str, threading.Thread] = {}

    def generate_report(
        self,
        analysis_results: Dict[str, Any],
        report_id: Optional[str] = None,
        title: str = "AI-Guard Analysis Report",
        description: str = "Comprehensive analysis report",
    ) -> ReportData:
        """Generate a comprehensive report."""
        report_id = report_id or f"report_{int(time.time())}"

        metrics = ReportMetrics()
        metrics.start_time = time.time()

        try:
            # Create report data structure
            report_data = ReportData(
                report_id=report_id,
                title=title,
                description=description,
                timestamp=datetime.now(timezone.utc),
                format=self.config.format,
                status=ReportStatus.GENERATING,
                metrics=metrics,
            )

            # Process entries in parallel if enabled
            if self.config.parallel_processing:
                entries = self._process_entries_parallel(analysis_results)
            else:
                entries = self._process_entries_sequential(analysis_results)

            report_data.entries = entries
            report_data.metrics.files_processed = len(
                set(entry.file_path for entry in entries)
            )
            report_data.metrics.issues_found = len(entries)

            # Generate summary
            report_data.summary = self._generate_summary(entries)

            # Update metrics
            metrics.end_time = time.time()
            metrics.generation_time_seconds = metrics.duration

            report_data.status = ReportStatus.COMPLETED

            # Record analytics
            self.analytics.record_generation(metrics)

            return report_data

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            metrics.end_time = time.time()
            report_data.status = ReportStatus.FAILED
            self.analytics.error_counts[str(e)] = (
                self.analytics.error_counts.get(str(e), 0) + 1
            )
            raise

    def _process_entries_parallel(
        self, analysis_results: Dict[str, Any]
    ) -> List[ReportEntry]:
        """Process entries using parallel processing."""
        issues = analysis_results.get("issues", [])
        if not issues:
            return []

        entries = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Split issues into chunks
            chunks = [
                issues[i : i + self.config.chunk_size]
                for i in range(0, len(issues), self.config.chunk_size)
            ]

            # Submit chunk processing tasks
            future_to_chunk = {
                executor.submit(self._process_chunk, chunk, i): i
                for i, chunk in enumerate(chunks)
            }

            # Collect results
            for future in as_completed(future_to_chunk):
                try:
                    chunk_entries = future.result()
                    entries.extend(chunk_entries)
                except Exception as e:
                    logger.error(f"Chunk processing failed: {e}")

        return entries

    def _process_chunk(
        self, issues_chunk: List[Dict[str, Any]], chunk_id: int
    ) -> List[ReportEntry]:
        """Process a chunk of issues."""
        entries = []

        for i, issue in enumerate(issues_chunk):
            entry_id = f"chunk_{chunk_id}_entry_{i}"

            entry = ReportEntry(
                id=entry_id,
                type=issue.get("type", "unknown"),
                severity=issue.get("severity", issue.get("level", "warning")),
                message=issue.get("message", ""),
                file_path=issue.get("file", issue.get("path", "unknown")),
                line_number=issue.get("line"),
                column_number=issue.get("column"),
                rule_id=issue.get("rule_id"),
                metadata=issue.get("metadata", {}),
            )

            entries.append(entry)

        return entries

    def _process_entries_sequential(
        self, analysis_results: Dict[str, Any]
    ) -> List[ReportEntry]:
        """Process entries sequentially."""
        issues = analysis_results.get("issues", [])
        entries = []

        for i, issue in enumerate(issues):
            entry = ReportEntry(
                id=f"entry_{i}",
                type=issue.get("type", "unknown"),
                severity=issue.get("severity", issue.get("level", "warning")),
                message=issue.get("message", ""),
                file_path=issue.get("file", issue.get("path", "unknown")),
                line_number=issue.get("line"),
                column_number=issue.get("column"),
                rule_id=issue.get("rule_id"),
                metadata=issue.get("metadata", {}),
            )

            entries.append(entry)

        return entries

    def _generate_summary(self, entries: List[ReportEntry]) -> Dict[str, Any]:
        """Generate report summary."""
        total_issues = len(entries)

        severity_counts = {}
        type_counts = {}
        file_counts = {}

        for entry in entries:
            # Count by severity
            severity_counts[entry.severity] = severity_counts.get(entry.severity, 0) + 1

            # Count by type
            type_counts[entry.type] = type_counts.get(entry.type, 0) + 1

            # Count by file
            file_counts[entry.file_path] = file_counts.get(entry.file_path, 0) + 1

        return {
            "total_issues": total_issues,
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "files_affected": len(file_counts),
            "top_files": sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ],
            "top_types": sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[
                :5
            ],
        }

    def export_report(
        self,
        report_data: ReportData,
        output_path: str,
        formats: Optional[List[ReportFormat]] = None,
    ) -> Dict[str, Any]:
        """Export report in multiple formats."""
        formats = formats or [self.config.format]
        results = {}

        for format_type in formats:
            try:
                if format_type not in self.processors:
                    results[format_type.value] = {
                        "success": False,
                        "error": f"Unsupported format: {format_type}",
                    }
                    continue

                processor = self.processors[format_type]

                # Check cache first
                cache_key = f"report_{report_data.report_id}_{format_type.value}"
                if self.config.enable_caching:
                    cached_result = self.cache_manager.get(cache_key)
                    if cached_result:
                        report_data.metrics.cache_hits += 1
                        results[format_type.value] = {
                            "success": True,
                            "from_cache": True,
                            "data": cached_result,
                        }
                        continue

                # Generate report content
                content = processor.process(report_data, self.config)

                # Apply compression if enabled
                if self.config.compress_output and format_type != ReportFormat.PDF:
                    content = gzip.compress(content)
                    report_data.metrics.compression_ratio = (
                        1
                        - len(content)
                        / len(processor.process(report_data, self.config))
                    ) * 100

                # Save to file
                file_path = self._get_output_path(output_path, format_type)
                with open(file_path, "wb") as f:
                    f.write(content)

                # Cache the result
                if self.config.enable_caching:
                    self.cache_manager.set(cache_key, content)
                    report_data.metrics.cache_misses += 1

                results[format_type.value] = {
                    "success": True,
                    "file_path": file_path,
                    "size_bytes": len(content),
                    "compressed": self.config.compress_output,
                }

            except Exception as e:
                logger.error(f"Export failed for {format_type}: {e}")
                results[format_type.value] = {"success": False, "error": str(e)}

        return results

    def _get_output_path(self, base_path: str, format_type: ReportFormat) -> str:
        """Get output file path for specific format."""
        path = Path(base_path)

        # Add format-specific extension if not present
        extensions = {
            ReportFormat.JSON: ".json",
            ReportFormat.HTML: ".html",
            ReportFormat.CSV: ".csv",
            ReportFormat.XML: ".xml",
            ReportFormat.PDF: ".pdf",
        }

        if format_type in extensions:
            if not path.suffix:
                path = path.with_suffix(extensions[format_type])
            elif self.config.compress_output and format_type != ReportFormat.PDF:
                path = path.with_suffix(path.suffix + ".gz")

        return str(path)

    async def generate_report_streaming(
        self,
        analysis_results: Dict[str, Any],
        report_id: Optional[str] = None,
        title: str = "AI-Guard Analysis Report",
        description: str = "Comprehensive analysis report",
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Generate report with streaming output."""
        if not self.config.streaming_enabled:
            raise ValueError("Streaming is not enabled in configuration")

        report_data = ReportData(
            report_id=report_id or f"report_{int(time.time())}",
            title=title,
            description=description,
            timestamp=datetime.now(timezone.utc),
            format=self.config.format,
            status=ReportStatus.GENERATING,
            metrics=ReportMetrics(),
        )

        try:
            # Stream report header
            header_data = self._generate_streaming_header(report_data)
            yield header_data

            if progress_callback:
                progress_callback(0.1)

            # Stream entries progressively
            issues = analysis_results.get("issues", [])
            total_issues = len(issues)

            for i, issue in enumerate(issues):
                entry = ReportEntry(
                    id=f"entry_{i}",
                    type=issue.get("type", "unknown"),
                    severity=issue.get("severity", issue.get("level", "warning")),
                    message=issue.get("message", ""),
                    file_path=issue.get("file", issue.get("path", "unknown")),
                    line_number=issue.get("line"),
                    column_number=issue.get("column"),
                    rule_id=issue.get("rule_id"),
                )

                entry_data = self._generate_streaming_entry(entry, report_data.format)
                yield entry_data

                if progress_callback:
                    progress = 0.1 + (0.8 * (i + 1) / total_issues)
                    progress_callback(progress)

                # Small delay to simulate streaming
                await asyncio.sleep(0.001)

            # Stream footer
            footer_data = self._generate_streaming_footer(report_data)
            yield footer_data

            if progress_callback:
                progress_callback(1.0)

        except Exception as e:
            logger.error(f"Streaming report generation failed: {e}")
            raise

    def _generate_streaming_header(self, report_data: ReportData) -> bytes:
        """Generate streaming report header."""
        if report_data.format == ReportFormat.JSON:
            return (
                b'{"report_id":"' + report_data.report_id.encode() + b'","entries":[\n'
            )
        elif report_data.format == ReportFormat.HTML:
            return (
                b"<html><head><title>"
                + report_data.title.encode()
                + b"</title></head><body><h1>"
                + report_data.title.encode()
                + b"</h1><table><tr><th>Type</th><th>Severity</th><th>File</th><th>Line</th><th>Message</th></tr>\n"
            )
        else:
            return b""

    def _generate_streaming_entry(
        self, entry: ReportEntry, format_type: ReportFormat
    ) -> bytes:
        """Generate streaming entry data."""
        if format_type == ReportFormat.JSON:
            entry_json = {
                "id": entry.id,
                "type": entry.type,
                "severity": entry.severity,
                "message": entry.message,
                "file_path": entry.file_path,
                "line_number": entry.line_number,
                "column_number": entry.column_number,
                "rule_id": entry.rule_id,
                "timestamp": entry.timestamp.isoformat(),
            }
            return json.dumps(entry_json).encode() + b",\n"
        elif format_type == ReportFormat.HTML:
            html = f'<tr><td>{entry.type}</td><td>{entry.severity}</td><td>{entry.file_path}</td><td>{entry.line_number or "-"}</td><td>{entry.message}</td></tr>\n'
            return html.encode()
        else:
            return b""

    def _generate_streaming_footer(self, report_data: ReportData) -> bytes:
        """Generate streaming report footer."""
        if report_data.format == ReportFormat.JSON:
            return b"]}\n"
        elif report_data.format == ReportFormat.HTML:
            return b"</table></body></html>\n"
        else:
            return b""

    def get_analytics(self) -> Dict[str, Any]:
        """Get report generation analytics."""
        return {
            "performance_stats": self.analytics.get_performance_stats(),
            "trend_analysis": self.analytics.get_trend_analysis(),
            "cache_stats": self.analytics.cache_stats,
            "error_counts": self.analytics.error_counts,
        }

    def cancel_generation(self, report_id: str) -> bool:
        """Cancel report generation."""
        if report_id in self._active_generations:
            thread = self._active_generations[report_id]
            # Note: Python threads cannot be forcefully killed
            # This is a placeholder for future implementation
            del self._active_generations[report_id]
            return True
        return False


class ReportScheduler:
    """Report scheduling and automation."""

    def __init__(self, generator: EnhancedReportGenerator):
        self.generator = generator
        self.scheduled_reports: Dict[str, Dict[str, Any]] = {}

    def schedule_report(
        self,
        schedule_id: str,
        analysis_results: Dict[str, Any],
        schedule_interval: int,  # seconds
        output_path: str,
        formats: List[ReportFormat],
    ) -> bool:
        """Schedule a recurring report."""
        self.scheduled_reports[schedule_id] = {
            "analysis_results": analysis_results,
            "schedule_interval": schedule_interval,
            "output_path": output_path,
            "formats": formats,
            "last_run": None,
            "next_run": time.time() + schedule_interval,
            "active": True,
        }
        return True

    def cancel_schedule(self, schedule_id: str) -> bool:
        """Cancel a scheduled report."""
        if schedule_id in self.scheduled_reports:
            self.scheduled_reports[schedule_id]["active"] = False
            return True
        return False

    def run_scheduled_reports(self) -> Dict[str, Any]:
        """Run all due scheduled reports."""
        current_time = time.time()
        results = {}

        for schedule_id, schedule in self.scheduled_reports.items():
            if not schedule["active"]:
                continue

            if current_time >= schedule["next_run"]:
                try:
                    report_data = self.generator.generate_report(
                        schedule["analysis_results"],
                        report_id=f"scheduled_{schedule_id}_{int(current_time)}",
                    )

                    export_results = self.generator.export_report(
                        report_data,
                        schedule["output_path"],
                        schedule["formats"],
                    )

                    results[schedule_id] = {
                        "success": True,
                        "export_results": export_results,
                    }

                    # Update schedule
                    schedule["last_run"] = current_time
                    schedule["next_run"] = current_time + schedule["schedule_interval"]

                except Exception as e:
                    logger.error(f"Scheduled report {schedule_id} failed: {e}")
                    results[schedule_id] = {
                        "success": False,
                        "error": str(e),
                    }

        return results


# Convenience functions for backward compatibility
def generate_enhanced_report(
    analysis_results: Dict[str, Any],
    format_type: str = "json",
    output_path: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Generate an enhanced report with the new system."""
    config = ReportConfig(format=ReportFormat(format_type), **kwargs)

    generator = EnhancedReportGenerator(config)
    report_data = generator.generate_report(analysis_results)

    if output_path:
        export_results = generator.export_report(report_data, output_path)
        return {
            "report_data": report_data,
            "export_results": export_results,
            "analytics": generator.get_analytics(),
        }

    return {
        "report_data": report_data,
        "analytics": generator.get_analytics(),
    }


def create_report_comparison(
    reports: List[ReportData], comparison_type: str = "trend"
) -> Dict[str, Any]:
    """Create a comparison report from multiple reports."""
    if len(reports) < 2:
        raise ValueError("At least 2 reports required for comparison")

    comparison_data = {
        "comparison_type": comparison_type,
        "report_count": len(reports),
        "time_range": {
            "start": min(r.timestamp for r in reports).isoformat(),
            "end": max(r.timestamp for r in reports).isoformat(),
        },
        "metrics_comparison": [],
        "trend_analysis": {},
    }

    # Compare metrics
    for i, report in enumerate(reports):
        metrics_summary = {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "total_issues": len(report.entries),
            "generation_time": report.metrics.duration,
            "files_processed": report.metrics.files_processed,
        }
        comparison_data["metrics_comparison"].append(metrics_summary)

    # Trend analysis
    if comparison_type == "trend":
        issue_counts = [len(r.entries) for r in reports]
        generation_times = [r.metrics.duration for r in reports]

        comparison_data["trend_analysis"] = {
            "issue_trend": (
                "increasing" if issue_counts[-1] > issue_counts[0] else "decreasing"
            ),
            "performance_trend": (
                "improving"
                if generation_times[-1] < generation_times[0]
                else "degrading"
            ),
            "issue_change_percent": (
                ((issue_counts[-1] - issue_counts[0]) / issue_counts[0] * 100)
                if issue_counts[0] > 0
                else 0
            ),
            "performance_change_percent": (
                (
                    (generation_times[-1] - generation_times[0])
                    / generation_times[0]
                    * 100
                )
                if generation_times[0] > 0
                else 0
            ),
        }

    return comparison_data
