"""Basic tests for analyzer.py module."""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, MagicMock

from src.ai_guard.analyzer import (
    RuleIdStyle,
    _rule_style,
    AnalysisConfig,
    AnalysisResult,
    SecurityAnalyzer,
    PerformanceAnalyzer,
    QualityAnalyzer,
    CoverageAnalyzer,
    CodeAnalyzer,
    run_analysis,
    generate_report,
)


class TestRuleIdStyle:
    """Test RuleIdStyle enum."""

    def test_rule_id_style_values(self):
        """Test RuleIdStyle enum values."""
        assert RuleIdStyle.BARE == "bare"
        assert RuleIdStyle.TOOL == "tool"


class TestRuleStyle:
    """Test _rule_style function."""

    def test_rule_style_default(self):
        """Test default rule style."""
        style = _rule_style()
        assert style in [RuleIdStyle.BARE, RuleIdStyle.TOOL]


class TestAnalysisConfig:
    """Test AnalysisConfig dataclass."""

    def test_analysis_config_default(self):
        """Test default AnalysisConfig creation."""
        config = AnalysisConfig()
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is True
        assert config.enable_coverage_analysis is True

    def test_analysis_config_custom(self):
        """Test custom AnalysisConfig creation."""
        config = AnalysisConfig(
            enable_security_analysis=False,
            enable_performance_analysis=True,
            enable_quality_analysis=False,
            enable_coverage_analysis=True
        )
        assert config.enable_security_analysis is False
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is False
        assert config.enable_coverage_analysis is True

    def test_analysis_config_from_dict(self):
        """Test AnalysisConfig creation from dictionary."""
        data = {
            "enable_security_analysis": False,
            "enable_performance_analysis": True,
            "enable_quality_analysis": False,
            "enable_coverage_analysis": True
        }
        config = AnalysisConfig.from_dict(data)
        assert config.enable_security_analysis is False
        assert config.enable_performance_analysis is True
        assert config.enable_quality_analysis is False
        assert config.enable_coverage_analysis is True


class TestAnalysisResult:
    """Test AnalysisResult dataclass."""

    def test_analysis_result_default(self):
        """Test default AnalysisResult creation."""
        result = AnalysisResult()
        assert result.security_issues == []
        assert result.performance_issues == []
        assert result.quality_issues == []
        assert result.coverage_data == {}
        assert result.execution_time == 0.0

    def test_analysis_result_custom(self):
        """Test custom AnalysisResult creation."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5
        )
        assert result.security_issues == ["issue1"]
        assert result.performance_issues == ["issue2"]
        assert result.quality_issues == ["issue3"]
        assert result.coverage_data == {"file1": 85.0}
        assert result.execution_time == 1.5

    def test_analysis_result_to_dict(self):
        """Test AnalysisResult to_dict method."""
        result = AnalysisResult(
            security_issues=["issue1"],
            performance_issues=["issue2"],
            quality_issues=["issue3"],
            coverage_data={"file1": 85.0},
            execution_time=1.5
        )
        data = result.to_dict()
        assert data["security_issues"] == ["issue1"]
        assert data["performance_issues"] == ["issue2"]
        assert data["quality_issues"] == ["issue3"]
        assert data["coverage_data"] == {"file1": 85.0}
        assert data["execution_time"] == 1.5