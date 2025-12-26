"""RESTful API for AI-Guard report generation and management."""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
    File,
    UploadFile,
    Form,
)
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from .report_optimized import (
    EnhancedReportGenerator,
    ReportConfig,
    ReportFormat,
    ReportType,
    ReportStatus,
    ReportData,
    ReportMetrics,
    ReportScheduler,
    generate_enhanced_report,
    create_report_comparison,
)

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# API Router
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# In-memory storage for demo (use database in production)
report_storage: Dict[str, Dict[str, Any]] = {}
scheduled_reports: Dict[str, Dict[str, Any]] = {}


# Pydantic Models
class ReportRequest(BaseModel):
    """Request model for report generation."""

    analysis_results: Dict[str, Any]
    title: str = "AI-Guard Analysis Report"
    description: str = "Comprehensive analysis report"
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
    export_formats: List[ReportFormat] = Field(default_factory=list)
    streaming_enabled: bool = True
    real_time_updates: bool = False


class ReportResponse(BaseModel):
    """Response model for report generation."""

    report_id: str
    status: ReportStatus
    title: str
    description: str
    timestamp: datetime
    format: ReportFormat
    metrics: Dict[str, Any]
    summary: Dict[str, Any]
    download_url: Optional[str] = None
    streaming_url: Optional[str] = None


class ReportListResponse(BaseModel):
    """Response model for report listing."""

    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int


class ReportComparisonRequest(BaseModel):
    """Request model for report comparison."""

    report_ids: List[str]
    comparison_type: str = "trend"


class ReportScheduleRequest(BaseModel):
    """Request model for report scheduling."""

    analysis_results: Dict[str, Any]
    schedule_interval: int = Field(..., description="Interval in seconds")
    output_path: str
    formats: List[ReportFormat]
    title: str = "Scheduled AI-Guard Report"
    description: str = "Automated report generation"


class ReportAnalyticsResponse(BaseModel):
    """Response model for report analytics."""

    performance_stats: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    cache_stats: Dict[str, Any]
    error_counts: Dict[str, Any]


class ReportExportRequest(BaseModel):
    """Request model for report export."""

    report_id: str
    formats: List[ReportFormat]
    output_path: Optional[str] = None


# Dependency injection
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Get current user from credentials."""
    # In production, implement proper authentication
    if credentials is None:
        return {"user_id": "anonymous", "role": "user"}

    # Validate token and return user info
    return {"user_id": "authenticated_user", "role": "admin"}


async def get_report_generator() -> EnhancedReportGenerator:
    """Get report generator instance."""
    config = ReportConfig(
        enable_caching=True,
        parallel_processing=True,
        streaming_enabled=True,
    )
    return EnhancedReportGenerator(config)


# API Endpoints


@router.post(
    "/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED
)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    generator: EnhancedReportGenerator = Depends(get_report_generator),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Generate a new report."""
    try:
        # Create report configuration
        config = ReportConfig(
            format=request.format,
            report_type=request.report_type,
            include_timestamp=request.include_timestamp,
            include_metadata=request.include_metadata,
            compress_output=request.compress_output,
            parallel_processing=request.parallel_processing,
            max_workers=request.max_workers,
            chunk_size=request.chunk_size,
            enable_caching=request.enable_caching,
            cache_ttl=request.cache_ttl,
            export_formats=request.export_formats,
            streaming_enabled=request.streaming_enabled,
            real_time_updates=request.real_time_updates,
        )

        # Generate report
        generator.config = config
        report_data = generator.generate_report(
            analysis_results=request.analysis_results,
            title=request.title,
            description=request.description,
        )

        # Store report
        report_storage[report_data.report_id] = {
            "data": report_data,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc),
        }

        # Schedule export if formats specified
        download_url = None
        if request.export_formats:
            background_tasks.add_task(
                export_report_background,
                report_data.report_id,
                request.export_formats,
                user["user_id"],
            )
            download_url = f"/api/v1/reports/{report_data.report_id}/download"

        streaming_url = None
        if request.streaming_enabled:
            streaming_url = f"/api/v1/reports/{report_data.report_id}/stream"

        return ReportResponse(
            report_id=report_data.report_id,
            status=report_data.status,
            title=report_data.title,
            description=report_data.description,
            timestamp=report_data.timestamp,
            format=report_data.format,
            metrics={
                "generation_time": report_data.metrics.duration,
                "files_processed": report_data.metrics.files_processed,
                "issues_found": report_data.metrics.issues_found,
                "memory_usage_mb": report_data.metrics.memory_usage_mb,
                "compression_ratio": report_data.metrics.compression_ratio,
            },
            summary=report_data.summary,
            download_url=download_url,
            streaming_url=streaming_url,
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    format_filter: Optional[ReportFormat] = None,
    status_filter: Optional[ReportStatus] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List all reports with pagination and filtering."""
    try:
        reports = list(report_storage.values())

        # Apply filters
        if format_filter:
            reports = [r for r in reports if r["data"].format == format_filter]
        if status_filter:
            reports = [r for r in reports if r["data"].status == status_filter]

        # Sort by creation date (newest first)
        reports.sort(key=lambda x: x["created_at"], reverse=True)

        # Pagination
        total = len(reports)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_reports = reports[start_idx:end_idx]

        # Convert to response format
        report_responses = []
        for report_info in paginated_reports:
            report_data = report_info["data"]
            report_responses.append(
                ReportResponse(
                    report_id=report_data.report_id,
                    status=report_data.status,
                    title=report_data.title,
                    description=report_data.description,
                    timestamp=report_data.timestamp,
                    format=report_data.format,
                    metrics={
                        "generation_time": report_data.metrics.duration,
                        "files_processed": report_data.metrics.files_processed,
                        "issues_found": report_data.metrics.issues_found,
                        "memory_usage_mb": report_data.metrics.memory_usage_mb,
                        "compression_ratio": report_data.metrics.compression_ratio,
                    },
                    summary=report_data.summary,
                    download_url=f"/api/v1/reports/{report_data.report_id}/download",
                    streaming_url=f"/api/v1/reports/{report_data.report_id}/stream",
                )
            )

        return ReportListResponse(
            reports=report_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}",
        )


# Health check endpoint (must come before /{report_id} route)
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
        "features": [
            "streaming_reports",
            "parallel_processing",
            "caching",
            "scheduling",
            "analytics",
            "multi_format_export",
        ],
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Get a specific report by ID."""
    if report_id not in report_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    try:
        report_info = report_storage[report_id]
        report_data = report_info["data"]

        return ReportResponse(
            report_id=report_data.report_id,
            status=report_data.status,
            title=report_data.title,
            description=report_data.description,
            timestamp=report_data.timestamp,
            format=report_data.format,
            metrics={
                "generation_time": report_data.metrics.duration,
                "files_processed": report_data.metrics.files_processed,
                "issues_found": report_data.metrics.issues_found,
                "memory_usage_mb": report_data.metrics.memory_usage_mb,
                "compression_ratio": report_data.metrics.compression_ratio,
            },
            summary=report_data.summary,
            download_url=f"/api/v1/reports/{report_id}/download",
            streaming_url=f"/api/v1/reports/{report_id}/stream",
        )

    except Exception as e:
        logger.error(f"Failed to get report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}",
        )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    format_type: Optional[ReportFormat] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Download a report in specific format."""
    if report_id not in report_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    try:
        report_info = report_storage[report_id]
        report_data = report_info["data"]

        # Use specified format or report's default format
        target_format = format_type or report_data.format

        # Generate file content
        generator = EnhancedReportGenerator()
        export_results = generator.export_report(
            report_data, f"temp_{report_id}", [target_format]
        )

        if not export_results.get(target_format.value, {}).get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to export report in {target_format.value} format",
            )

        file_path = export_results[target_format.value]["file_path"]

        # Determine content type
        content_types = {
            ReportFormat.JSON: "application/json",
            ReportFormat.HTML: "text/html",
            ReportFormat.CSV: "text/csv",
            ReportFormat.XML: "application/xml",
            ReportFormat.PDF: "application/pdf",
        }

        content_type = content_types.get(target_format, "application/octet-stream")

        # Generate filename
        filename = f"ai-guard-report-{report_id}.{target_format.value}"
        if export_results[target_format.value].get("compressed", False):
            filename += ".gz"

        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Failed to download report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report: {str(e)}",
        )


@router.get("/{report_id}/stream")
async def stream_report(
    report_id: str,
    format_type: Optional[ReportFormat] = None,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Stream a report for real-time viewing."""
    if report_id not in report_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    try:
        report_info = report_storage[report_id]
        report_data = report_info["data"]

        # Use specified format or report's default format
        target_format = format_type or report_data.format

        # Create streaming generator
        generator = EnhancedReportGenerator()
        config = ReportConfig(format=target_format, streaming_enabled=True)
        generator.config = config

        async def generate_stream():
            async for chunk in generator.generate_report_streaming(
                analysis_results={
                    "issues": [entry.__dict__ for entry in report_data.entries]
                },
                report_id=report_id,
                title=report_data.title,
                description=report_data.description,
            ):
                yield chunk

        # Determine content type
        content_types = {
            ReportFormat.JSON: "application/json",
            ReportFormat.HTML: "text/html",
            ReportFormat.CSV: "text/csv",
            ReportFormat.XML: "application/xml",
        }

        content_type = content_types.get(target_format, "application/octet-stream")

        return StreamingResponse(
            generate_stream(),
            media_type=content_type,
            headers={"Cache-Control": "no-cache"},
        )

    except Exception as e:
        logger.error(f"Failed to stream report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream report: {str(e)}",
        )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a report."""
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to delete reports",
        )

    if report_id not in report_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    try:
        del report_storage[report_id]
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        logger.error(f"Failed to delete report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}",
        )


@router.post("/compare")
async def compare_reports(
    request: ReportComparisonRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Compare multiple reports."""
    try:
        # Validate report IDs
        for report_id in request.report_ids:
            if report_id not in report_storage:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report {report_id} not found",
                )

        # Get report data
        reports = [
            report_storage[report_id]["data"] for report_id in request.report_ids
        ]

        # Create comparison
        comparison_data = create_report_comparison(reports, request.comparison_type)

        return comparison_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare reports: {str(e)}",
        )


@router.post("/schedule")
async def schedule_report(
    request: ReportScheduleRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Schedule a recurring report."""
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to schedule reports",
        )

    try:
        schedule_id = str(uuid.uuid4())

        scheduled_reports[schedule_id] = {
            "analysis_results": request.analysis_results,
            "schedule_interval": request.schedule_interval,
            "output_path": request.output_path,
            "formats": request.formats,
            "title": request.title,
            "description": request.description,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc),
            "last_run": None,
            "next_run": datetime.now(timezone.utc).timestamp()
            + request.schedule_interval,
            "active": True,
        }

        return {"schedule_id": schedule_id, "status": "scheduled"}

    except Exception as e:
        logger.error(f"Failed to schedule report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule report: {str(e)}",
        )


@router.get("/schedule/", response_model=List[Dict[str, Any]])
async def list_scheduled_reports(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List all scheduled reports."""
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view scheduled reports",
        )

    try:
        return list(scheduled_reports.values())

    except Exception as e:
        logger.error(f"Failed to list scheduled reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scheduled reports: {str(e)}",
        )


@router.delete("/schedule/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_scheduled_report(
    schedule_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Cancel a scheduled report."""
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to cancel scheduled reports",
        )

    if schedule_id not in scheduled_reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheduled report {schedule_id} not found",
        )

    try:
        del scheduled_reports[schedule_id]
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        logger.error(f"Failed to cancel scheduled report {schedule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel scheduled report: {str(e)}",
        )


@router.get("/analytics/performance", response_model=ReportAnalyticsResponse)
async def get_report_analytics(
    generator: EnhancedReportGenerator = Depends(get_report_generator),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Get report generation analytics."""
    try:
        analytics = generator.get_analytics()

        return ReportAnalyticsResponse(
            performance_stats=analytics["performance_stats"],
            trend_analysis=analytics["trend_analysis"],
            cache_stats=analytics["cache_stats"],
            error_counts=analytics["error_counts"],
        )

    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}",
        )


@router.post("/upload")
async def upload_analysis_results(
    file: UploadFile = File(...),
    title: str = Form("Uploaded Analysis Report"),
    description: str = Form("Report generated from uploaded analysis results"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Upload analysis results file and generate report."""
    try:
        # Read file content
        content = await file.read()

        # Parse based on file type
        if file.filename.endswith(".json"):
            analysis_results = json.loads(content.decode("utf-8"))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON files are supported",
            )

        # Generate report
        generator = EnhancedReportGenerator()
        report_data = generator.generate_report(
            analysis_results=analysis_results,
            title=title,
            description=description,
        )

        # Store report
        report_storage[report_data.report_id] = {
            "data": report_data,
            "created_by": user["user_id"],
            "created_at": datetime.now(timezone.utc),
            "source": "upload",
            "filename": file.filename,
        }

        return ReportResponse(
            report_id=report_data.report_id,
            status=report_data.status,
            title=report_data.title,
            description=report_data.description,
            timestamp=report_data.timestamp,
            format=report_data.format,
            metrics={
                "generation_time": report_data.metrics.duration,
                "files_processed": report_data.metrics.files_processed,
                "issues_found": report_data.metrics.issues_found,
                "memory_usage_mb": report_data.metrics.memory_usage_mb,
                "compression_ratio": report_data.metrics.compression_ratio,
            },
            summary=report_data.summary,
            download_url=f"/api/v1/reports/{report_data.report_id}/download",
            streaming_url=f"/api/v1/reports/{report_data.report_id}/stream",
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format"
        )
    except Exception as e:
        logger.error(f"Failed to upload and process file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}",
        )


# Background tasks
async def export_report_background(
    report_id: str,
    formats: List[ReportFormat],
    user_id: str,
):
    """Background task to export report."""
    try:
        if report_id not in report_storage:
            logger.error(f"Report {report_id} not found for export")
            return

        report_info = report_storage[report_id]
        report_data = report_info["data"]

        generator = EnhancedReportGenerator()
        export_results = generator.export_report(
            report_data, f"exports/{report_id}", formats
        )

        # Update report storage with export results
        report_info["exports"] = export_results

        logger.info(f"Report {report_id} exported successfully")

    except Exception as e:
        logger.error(f"Background export failed for report {report_id}: {e}")


# WebSocket endpoint for real-time updates
@router.websocket("/ws/updates")
async def websocket_updates(websocket):
    """WebSocket endpoint for real-time report updates."""
    await websocket.accept()

    try:
        while True:
            # Send periodic updates about report generation status
            active_reports = [
                report_id
                for report_id, report_info in report_storage.items()
                if report_info["data"].status == ReportStatus.GENERATING
            ]

            await websocket.send_json(
                {
                    "type": "status_update",
                    "active_reports": active_reports,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            await asyncio.sleep(5)  # Update every 5 seconds

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


# Create FastAPI app
def create_report_api_app() -> APIRouter:
    """Create and configure the report API router."""
    return router


# Standalone server (for testing)
def run_report_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the report API server."""
    from fastapi import FastAPI

    app = FastAPI(
        title="AI-Guard Report API",
        description="Enhanced reporting system with streaming, analytics, and automation",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(router)

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_report_server()
