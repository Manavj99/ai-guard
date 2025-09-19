"""
AI-Guard: Smart Code Quality Gatekeeper for AI-generated code.

AI Guard is a comprehensive code quality assurance tool designed specifically
for AI-generated code. It provides automated testing, security scanning,
performance monitoring, and quality gates to ensure that AI-generated code
meets enterprise-grade standards before integration into production systems.

Key Features:
- Comprehensive code analysis with static analysis tools
- Automated test generation and coverage analysis
- Security scanning and vulnerability detection
- Performance monitoring and optimization
- Multi-language support (Python, JavaScript, TypeScript)
- Rich reporting in multiple formats (SARIF, JSON, HTML)
- CI/CD integration with GitHub Actions

Example:
    >>> from ai_guard import Gates
    >>> gates = Gates()
    >>> result = gates.run_analysis("src/")
    >>> print(f"Analysis completed: {result.summary}")
"""

__version__ = "0.1.0"
__author__ = "AI-Guard Contributors"
__email__ = "support@ai-guard.dev"
__license__ = "MIT"
__url__ = "https://github.com/ai-guard/ai-guard"

from .config import Gates
from .report import GateResult, summarize

__all__ = ["Gates", "GateResult", "summarize", "__version__", "__author__"]
