"""AI-Guard: Smart Code Quality Gatekeeper for AI-generated code."""

__version__ = "0.1.0"
__author__ = "AI-Guard Contributors"

from .config import Gates
from .report import GateResult, summarize

__all__ = ["Gates", "GateResult", "summarize"]
