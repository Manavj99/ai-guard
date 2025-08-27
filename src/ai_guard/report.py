"""Reporting and result aggregation for AI-Guard."""

from dataclasses import dataclass
from typing import List


@dataclass
class GateResult:
    """Result of a quality gate check."""
    
    name: str
    passed: bool
    details: str = ""
    exit_code: int = 0


def summarize(results: List[GateResult]) -> int:
    """Summarize all gate results and return overall exit code.
    
    Args:
        results: List of gate results
        
    Returns:
        0 if all gates passed, 1 if any failed
    """
    failed = [r for r in results if not r.passed]
    
    print("\n" + "="*50)
    print("AI-Guard Quality Gates Summary")
    print("="*50)
    
    for result in results:
        prefix = "✅" if result.passed else "❌"
        status = "PASSED" if result.passed else "FAILED"
        details = f" - {result.details}" if result.details else ""
        print(f"{prefix} {result.name}: {status}{details}")
    
    print("="*50)
    
    if failed:
        print(f"❌ {len(failed)} gate(s) failed")
        return 1
    else:
        print("✅ All gates passed!")
        return 0
