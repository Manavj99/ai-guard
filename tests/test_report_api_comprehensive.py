"""Comprehensive tests for report_api.py module."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.ai_guard.report_api import (
    ReportRequest,
    ReportResponse,
    ReportListResponse,
    router,
    get_current_user,
    get_report_generator,
)


class TestModels:
    """Test Pydantic models."""

    def test_report_request(self):
        """Test ReportRequest model."""
        request = ReportRequest(
            analysis_results={"key": "value"},
            title="Test Report",
            format="json",
        )
        assert request.title == "Test Report"
        assert request.analysis_results == {"key": "value"}

    def test_report_response(self):
        """Test ReportResponse model."""
        response = ReportResponse(
            report_id="test_123",
            status="completed",
            title="Test",
            description="Test",
            timestamp=datetime.now(),
            format="json",
            metrics={},
            summary={},
        )
        assert response.report_id == "test_123"


@pytest.mark.asyncio
async def test_get_current_user_no_credentials():
    """Test getting current user without credentials."""
    user = await get_current_user(credentials=None)
    assert user["user_id"] == "anonymous"


@pytest.mark.asyncio
async def test_get_current_user_with_credentials():
    """Test getting current user with credentials."""
    mock_creds = MagicMock()
    user = await get_current_user(credentials=mock_creds)
    assert user["user_id"] == "authenticated_user"


@pytest.mark.asyncio
async def test_get_report_generator():
    """Test getting report generator."""
    generator = await get_report_generator()
    assert generator is not None


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    from src.ai_guard.report_api import health_check

    response = await health_check()
    assert response["status"] == "healthy"
