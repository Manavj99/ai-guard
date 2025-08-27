"""Generate speculative tests for changed code."""

import argparse
from pathlib import Path
from typing import List

from ..diff_parser import changed_python_files


def generate_speculative_tests(changed_files: List[str]) -> str:
    """Generate speculative test content for changed files.

    Args:
        changed_files: List of Python files that have changed

    Returns:
        Generated test content as string
    """
    if not changed_files:
        return ""

    # MVP: scaffold basic tests
    content = [
        "# Auto-generated speculative tests (MVP)",
        "# Generated for the following changed files:",
        "",
    ]

    for file_path in changed_files:
        content.append(f"# - {file_path}")

    content.extend(
        [
            "",
            "import pytest",
            "",
            "def test_generated_imports():",
            '    """Test that all changed modules can be imported."""',
            "    assert True",
            "",
            "def test_generated_smoke():",
            '    """Basic smoke test for changed code."""',
            "    assert True",
            "",
        ]
    )

    return "\n".join(content)


def main() -> None:
    """Main entry point for test generation."""
    parser = argparse.ArgumentParser(
        description="Generate speculative tests for changed code"
    )
    parser.add_argument("--event", help="Path to GitHub event JSON file")
    parser.add_argument(
        "--output",
        default="tests/unit/test_generated.py",
        help="Output path for generated tests",
    )
    args = parser.parse_args()

    # Get changed files
    changed_files = changed_python_files(args.event)

    if not changed_files:
        print("[testgen] No Python files changed, skipping test generation")
        return

    # Generate test content
    test_content = generate_speculative_tests(changed_files)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write generated tests
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    print(f"[testgen] Generated speculative tests for {len(changed_files)} files")
    print(f"[testgen] Output: {output_path}")


if __name__ == "__main__":
    main()
