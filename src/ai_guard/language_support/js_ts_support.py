"""JavaScript/TypeScript language support for AI-Guard."""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


def check_node_installed() -> bool:
    """Check if Node.js is installed and available.

    Returns:
        True if Node.js is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_npm_installed() -> bool:
    """Check if npm is installed and available.

    Returns:
        True if npm is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["npm", "--version"], capture_output=True, text=True, check=True
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_eslint(files: List[str]) -> Dict[str, Any]:
    """Run ESLint on JavaScript/TypeScript files.

    Args:
        files: List of files to check

    Returns:
        Dictionary with ESLint results
    """
    try:
        cmd = ["npx", "eslint"] + files
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return {
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "output": "",
            "errors": "ESLint not found",
            "returncode": 1,
        }


def run_typescript_check(files: List[str]) -> Dict[str, Any]:
    """Run TypeScript compiler check on files.

    Args:
        files: List of TypeScript files to check

    Returns:
        Dictionary with TypeScript check results
    """
    try:
        cmd = ["npx", "tsc", "--noEmit"] + files
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return {
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "output": "",
            "errors": "TypeScript compiler not found",
            "returncode": 1,
        }


def run_jest_tests() -> Dict[str, Any]:
    """Run Jest tests.

    Returns:
        Dictionary with Jest test results
    """
    try:
        cmd = ["npx", "jest", "--passWithNoTests"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return {
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "output": "",
            "errors": "Jest not found",
            "returncode": 1,
        }


def run_prettier_check(files: List[str]) -> Dict[str, Any]:
    """Run Prettier check on files.

    Args:
        files: List of files to check

    Returns:
        Dictionary with Prettier check results
    """
    try:
        cmd = ["npx", "prettier", "--check"] + files
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        return {
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "output": "",
            "errors": "Prettier not found",
            "returncode": 1,
        }


@dataclass
class JSTestGenerationConfig:
    """Configuration for JavaScript/TypeScript test generation."""

    # Test Framework
    test_framework: str = "jest"  # jest, vitest, mocha
    test_runner: str = "npm test"

    # Code Quality Tools
    use_eslint: bool = True
    use_prettier: bool = True
    use_typescript: bool = False

    # Test Generation Settings
    generate_unit_tests: bool = True
    generate_integration_tests: bool = False
    generate_mocks: bool = True
    generate_snapshots: bool = True

    # Output Settings
    output_directory: str = "tests"
    test_file_suffix: str = ".test.js"
    include_types: bool = True


@dataclass
class JSFileChange:
    """Represents a JavaScript/TypeScript file change."""

    file_path: str
    function_name: Optional[str]
    class_name: Optional[str]
    change_type: str  # function, class, import, etc.
    line_numbers: Tuple[int, int]
    code_snippet: str
    context: str


class JavaScriptTypeScriptSupport:
    """JavaScript/TypeScript language support for AI-Guard."""

    def __init__(self, config: JSTestGenerationConfig):
        self.config = config
        self.project_root = self._find_project_root()
        self.package_json = self._load_package_json()

    def _find_project_root(self) -> Path:
        """Find the project root directory (where package.json is located)."""
        current = Path.cwd()

        while current != current.parent:
            if (current / "package.json").exists():
                return current
            current = current.parent

        return Path.cwd()

    def _load_package_json(self) -> Dict[str, Any]:
        """Load package.json configuration."""
        package_path = self.project_root / "package.json"

        if not package_path.exists():
            logger.warning("No package.json found, using default configuration")
            return {}

        try:
            with open(package_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
        except Exception as e:
            logger.warning(f"Error loading package.json: {e}")
            return {}

    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are installed."""
        dependencies = {
            "eslint": False,
            "prettier": False,
            "jest": False,
            "typescript": False,
        }

        # Check package.json dependencies
        deps = self.package_json.get("dependencies", {})
        dev_deps = self.package_json.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}

        if "eslint" in all_deps:
            dependencies["eslint"] = True

        if "prettier" in all_deps:
            dependencies["prettier"] = True

        if "jest" in all_deps:
            dependencies["jest"] = True

        if "typescript" in all_deps:
            dependencies["typescript"] = True

        # Check if tools are available in PATH
        try:
            subprocess.run(["eslint", "--version"], capture_output=True, check=False)
            dependencies["eslint"] = True
        except FileNotFoundError:
            pass

        try:
            subprocess.run(["prettier", "--version"], capture_output=True, check=False)
            dependencies["prettier"] = True
        except FileNotFoundError:
            pass

        try:
            subprocess.run(["jest", "--version"], capture_output=True, check=False)
            dependencies["jest"] = True
        except FileNotFoundError:
            pass

        try:
            subprocess.run(["tsc", "--version"], capture_output=True, check=False)
            dependencies["typescript"] = True
        except FileNotFoundError:
            pass

        return dependencies

    def run_eslint(self, file_paths: List[str]) -> Tuple[bool, List[Dict[str, Any]]]:
        """Run ESLint on specified files."""
        if not self.config.use_eslint:
            return True, []

        try:
            # Check if ESLint is available
            deps = self.check_dependencies()
            if not deps["eslint"]:
                logger.warning("ESLint not available, skipping linting")
                return True, []

            # Run ESLint
            cmd = ["npx", "eslint", "--format", "json"] + file_paths
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                return True, []

            # Parse ESLint output
            try:
                eslint_results = json.loads(result.stdout)
                issues = []

                for file_result in eslint_results:
                    for message in file_result.get("messages", []):
                        issues.append(
                            {
                                "file": file_result["filePath"],
                                "line": message.get("line", 0),
                                "column": message.get("column", 0),
                                "severity": message.get("severity", 1),
                                "message": message.get("message", ""),
                                "rule": message.get("ruleId", ""),
                            }
                        )

                return False, issues

            except json.JSONDecodeError:
                logger.warning("Could not parse ESLint output")
                return False, [{"error": "ESLint parsing failed"}]

        except Exception as e:
            logger.error(f"ESLint execution failed: {e}")
            return False, [{"error": str(e)}]

    def run_prettier(self, file_paths: List[str]) -> Tuple[bool, List[str]]:
        """Run Prettier on specified files."""
        if not self.config.use_prettier:
            return True, []

        try:
            # Check if Prettier is available
            deps = self.check_dependencies()
            if not deps["prettier"]:
                logger.warning("Prettier not available, skipping formatting")
                return True, []

            # Run Prettier check
            cmd = ["npx", "prettier", "--check"] + file_paths
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                return True, []

            # Get list of files that need formatting
            formatted_files = []
            for line in result.stdout.split("\n"):
                if line.strip() and not line.startswith("["):
                    formatted_files.append(line.strip())

            return False, formatted_files

        except Exception as e:
            logger.error(f"Prettier execution failed: {e}")
            return False, [str(e)]

    def run_typescript_check(
        self, file_paths: List[str]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Run TypeScript type checking on specified files."""
        if not self.config.use_typescript:
            return True, []

        try:
            # Check if TypeScript is available
            deps = self.check_dependencies()
            if not deps["typescript"]:
                logger.warning("TypeScript not available, skipping type checking")
                return True, []

            # Run TypeScript compiler
            cmd = ["npx", "tsc", "--noEmit", "--pretty", "false"]

            # Add TypeScript files
            ts_files = [f for f in file_paths if f.endswith((".ts", ".tsx"))]
            if not ts_files:
                return True, []

            cmd.extend(ts_files)

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                return True, []

            # Parse TypeScript output
            issues = []
            for line in result.stderr.split("\n"):
                if line.strip() and ":" in line:
                    # Parse TypeScript error format: file(line,col): error TS1234: message
                    parts = line.split(":", 3)
                    if len(parts) >= 4:
                        file_path = parts[0]
                        location = parts[1]
                        error_code = parts[2].strip()
                        message = parts[3].strip()

                        # Extract line and column from location
                        loc_match = location.strip("()").split(",")
                        line_num = int(loc_match[0]) if loc_match else 0
                        col_num = int(loc_match[1]) if len(loc_match) > 1 else 0

                        issues.append(
                            {
                                "file": file_path,
                                "line": line_num,
                                "column": col_num,
                                "severity": 2,  # Error
                                "message": message,
                                "rule": error_code,
                            }
                        )

            return False, issues

        except Exception as e:
            logger.error(f"TypeScript check failed: {e}")
            return False, [{"error": str(e)}]

    def run_jest_tests(
        self, test_pattern: str = "**/*.test.js"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Run Jest tests and return results."""
        try:
            # Check if Jest is available
            deps = self.check_dependencies()
            if not deps["jest"]:
                logger.warning("Jest not available, skipping tests")
                return True, {"message": "Jest not available"}

            # Run Jest
            cmd = ["npx", "jest", "--json", "--silent"]
            if test_pattern:
                cmd.append(test_pattern)

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                return True, {"message": "All tests passed"}

            # Parse Jest output
            try:
                jest_results = json.loads(result.stdout)
                return False, jest_results
            except json.JSONDecodeError:
                return False, {"message": "Tests failed", "output": result.stdout}

        except Exception as e:
            logger.error(f"Jest execution failed: {e}")
            return False, {"error": str(e)}

    def generate_test_templates(self, file_paths: List[str]) -> Dict[str, str]:
        """Generate test templates for JavaScript/TypeScript files."""
        templates = {}

        for file_path in file_paths:
            if not file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Generate test template based on file content
                test_content = self._create_test_template(file_path, content)
                if test_content:
                    templates[file_path] = test_content

            except Exception as e:
                logger.warning(f"Error reading {file_path}: {e}")

        return templates

    def _create_test_template(self, file_path: str, content: str) -> str:
        """Create a test template for a JavaScript/TypeScript file."""
        file_name = Path(file_path).stem
        file_ext = Path(file_path).suffix

        # Determine if it's TypeScript
        is_typescript = file_ext in (".ts", ".tsx")

        # Basic test template
        if self.config.test_framework == "jest":
            template = f"""// Auto-generated test file for {file_path}
import {{ render, screen }} from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Import the module to test
{(f"import {{ {file_name} }} from './{file_name}';" if is_typescript
  else f"const {{ {file_name} }} = require('./{file_name}');")}

describe('{file_name}', () => {{
  test('should render without crashing', () => {{
    // TODO: Implement test
    expect(true).toBe(true);
  }});

  test('should handle user interactions', () => {{
    // TODO: Implement test
    expect(true).toBe(true);
  }});

  test('should handle edge cases', () => {{
    // TODO: Implement test
    expect(true).toBe(true);
  }});
}});
"""
        else:
            # Generic test template
            template = f"""// Auto-generated test file for {file_path}
// TODO: Implement tests using your preferred testing framework

// Import the module to test
{(f"import {{ {file_name} }} from './{file_name}';" if is_typescript
  else f"const {{ {file_name} }} = require('./{file_name}');")}

// Add your tests here
"""

        return template

    def create_test_file(self, file_path: str, test_content: str) -> str:
        """Create a test file path and content."""
        file_path_obj = Path(file_path)
        test_dir = Path(self.config.output_directory)
        test_file = test_dir / f"{file_path_obj.stem}{self.config.test_file_suffix}"

        # Ensure test directory exists
        test_dir.mkdir(parents=True, exist_ok=True)

        # Write test file
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        return str(test_file)

    def run_quality_checks(self, file_paths: List[str]) -> Dict[str, Any]:
        """Run all quality checks for JavaScript/TypeScript files."""
        results = {
            "eslint": {"passed": True, "issues": []},
            "prettier": {"passed": True, "issues": []},
            "typescript": {"passed": True, "issues": []},
            "overall": True,
        }

        # Run ESLint
        if self.config.use_eslint:
            eslint_passed, eslint_issues = self.run_eslint(file_paths)
            results["eslint"] = {"passed": eslint_passed, "issues": eslint_issues}
            if not eslint_passed:
                results["overall"] = False

        # Run Prettier
        if self.config.use_prettier:
            prettier_passed, prettier_issues = self.run_prettier(file_paths)
            results["prettier"] = {"passed": prettier_passed, "issues": prettier_issues}
            if not prettier_passed:
                results["overall"] = False

        # Run TypeScript check
        if self.config.use_typescript:
            ts_passed, ts_issues = self.run_typescript_check(file_paths)
            results["typescript"] = {"passed": ts_passed, "issues": ts_issues}
            if not ts_passed:
                results["overall"] = False

        return results

    def generate_tests(self, file_paths: List[str]) -> Dict[str, str]:
        """Generate tests for JavaScript/TypeScript files."""
        if not self.config.generate_unit_tests:
            return {}

        # Generate test templates
        templates = self.generate_test_templates(file_paths)

        # Create test files
        created_files = {}
        for file_path, test_content in templates.items():
            test_file = self.create_test_file(file_path, test_content)
            created_files[file_path] = test_file

        return created_files

    def run_linting(self, file_path: str) -> Dict[str, Any]:
        """Run linting on a single file or directory."""
        try:
            if Path(file_path).is_dir():
                # If it's a directory, find all JS/TS files
                js_files: list[Path] = []
                for ext in ["*.js", "*.jsx", "*.ts", "*.tsx"]:
                    js_files.extend(Path(file_path).glob(f"**/{ext}"))
                file_paths = [str(f) for f in js_files]
            else:
                file_paths = [file_path]

            if not file_paths:
                return {"success": True, "output": "No JavaScript/TypeScript files found"}

            # Run ESLint
            passed, issues = self.run_eslint(file_paths)

            if passed:
                return {"success": True, "output": "Linting passed"}
            else:
                output = "Linting failed\n"
                for issue in issues[:5]:  # Show first 5 issues
                    if isinstance(issue, dict) and "message" in issue:
                        output += f"- {issue['message']}\n"
                return {"success": False, "output": output.strip()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_testing(self) -> Dict[str, Any]:
        """Run tests using the configured test runner."""
        try:
            # Check if Jest is available
            deps = self.check_dependencies()
            if not deps["jest"]:
                return {"success": False, "error": "Jest not available"}

            # Run Jest tests
            passed, result = self.run_jest_tests()

            if passed:
                return {"success": True, "output": "Tests passed"}
            else:
                return {"success": False, "output": "Tests failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_test_file_path(self, source_file_path: str) -> str:
        """Generate test file path for a source file."""
        source_path = Path(source_file_path)

        # Get relative path from project root
        try:
            rel_path = source_path.relative_to(self.project_root)
        except ValueError:
            # If not relative to project root, use the filename
            rel_path = Path(source_path.name)

        # Create test file path
        test_dir = Path(self.config.output_directory)
        test_file_name = f"{rel_path.stem}{self.config.test_file_suffix}"

        # Handle the case where rel_path.parent might be empty
        if rel_path.parent == Path('.'):
            test_path = test_dir / test_file_name
        else:
            test_path = test_dir / rel_path.parent / test_file_name

        return str(test_path)

    def analyze_file_changes(self, changes: List[JSFileChange]) -> Dict[str, Dict[str, List[str]]]:
        """Analyze file changes and group by file."""
        analysis: dict[str, Any] = {}

        for change in changes:
            file_name = Path(change.file_path).name

            if file_name not in analysis:
                analysis[file_name] = {
                    "functions": [],
                    "classes": [],
                    "imports": []
                }

            if change.function_name:
                analysis[file_name]["functions"].append(change.function_name)

            if change.class_name:
                analysis[file_name]["classes"].append(change.class_name)

            if change.change_type == "import":
                analysis[file_name]["imports"].append(change.code_snippet)

        return analysis

    def generate_test_content(self, change: JSFileChange) -> str:
        """Generate test content for a specific file change."""
        file_name = Path(change.file_path).stem
        is_typescript = change.file_path.endswith(('.ts', '.tsx'))

        if change.change_type == "function" and change.function_name:
            return self._generate_function_test(change.function_name, change.code_snippet, is_typescript)
        elif change.change_type == "class" and change.class_name:
            return self._generate_class_test(change.class_name, change.code_snippet, is_typescript)
        else:
            return self._generate_generic_test(file_name, is_typescript)

    def _generate_function_test(self, function_name: str, code_snippet: str, is_typescript: bool) -> str:
        """Generate test content for a function."""

        return f"""// Auto-generated test for function: {function_name}
import {{ {function_name} }} from './{function_name}';

describe('{function_name}', () => {{
  test('should work correctly', () => {{
    // TODO: Implement test for {function_name}
    expect(true).toBe(true);
  }});
}});
"""

    def _generate_class_test(self, class_name: str, code_snippet: str, is_typescript: bool) -> str:
        """Generate test content for a class."""

        return f"""// Auto-generated test for class: {class_name}
import {{ {class_name} }} from './{class_name}';

describe('{class_name}', () => {{
  test('should instantiate correctly', () => {{
    // TODO: Implement test for {class_name}
    expect(true).toBe(true);
  }});
}});
"""

    def _generate_generic_test(self, file_name: str, is_typescript: bool) -> str:
        """Generate generic test content."""

        return f"""// Auto-generated test for {file_name}
import {{ {file_name} }} from './{file_name}';

describe('{file_name}', () => {{
  test('should work correctly', () => {{
    // TODO: Implement test
    expect(true).toBe(true);
  }});
}});
"""

    def validate_code_quality(self, file_path: str) -> Dict[str, Any]:
        """Validate code quality for a file or directory."""
        try:
            # Run linting
            linting_result = self.run_linting(file_path)

            # Run testing
            testing_result = self.run_testing()

            return {
                "overall_success": linting_result["success"] and testing_result["success"],
                "linting": linting_result,
                "testing": testing_result
            }
        except Exception as e:
            return {
                "overall_success": False,
                "linting": {"success": False, "error": str(e)},
                "testing": {"success": False, "error": str(e)}
            }

    def get_recommendations(self, analysis: Dict[str, Dict[str, List[str]]]) -> List[str]:
        """Get recommendations based on analysis results."""
        recommendations = []

        for file_name, file_analysis in analysis.items():
            functions = file_analysis.get("functions", [])
            classes = file_analysis.get("classes", [])

            if functions:
                recommendations.append(
                    f"Consider adding unit tests for {len(functions)} functions in {file_name}")

            if classes:
                recommendations.append(
                    f"Consider adding unit tests for {len(classes)} classes in {file_name}")

            if not functions and not classes:
                recommendations.append(
                    f"No functions or classes found in {file_name} - consider adding test coverage")

        if not recommendations:
            recommendations.append("No specific recommendations at this time")

        return recommendations

    def export_results(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Export analysis results with metadata."""
        from datetime import datetime

        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "config": {
                "test_framework": self.config.test_framework,
                "use_eslint": self.config.use_eslint,
                "use_prettier": self.config.use_prettier,
                "use_typescript": self.config.use_typescript,
                "output_directory": self.config.output_directory,
                "test_file_suffix": self.config.test_file_suffix
            },
            "project_root": str(self.project_root),
            "package_json": self.package_json
        }


def main() -> None:
    """Main entry point for JavaScript/TypeScript support."""
    import argparse

    parser = argparse.ArgumentParser(
        description="JavaScript/TypeScript language support for AI-Guard"
    )
    parser.add_argument("--files", nargs="+", help="Files to analyze")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--quality", action="store_true", help="Run quality checks")
    parser.add_argument(
        "--generate-tests", action="store_true", help="Generate test files"
    )
    parser.add_argument(
        "--output-dir", default="tests", help="Output directory for tests"
    )

    args = parser.parse_args()

    # Initialize support
    config = JSTestGenerationConfig(output_directory=args.output_dir)
    support = JavaScriptTypeScriptSupport(config)

    if args.check_deps:
        deps = support.check_dependencies()
        print("Dependencies:")
        for dep, available in deps.items():
            status = "✅" if available else "❌"
            print(f"  {status} {dep}")

    if args.files and args.quality:
        results = support.run_quality_checks(args.files)
        print("\nQuality Check Results:")
        for tool, result in results.items():
            if tool == "overall":
                continue
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"  {tool}: {status}")
            if not result["passed"] and result["issues"]:
                for issue in result["issues"][:3]:  # Show first 3 issues
                    if isinstance(issue, dict):
                        if "message" in issue:
                            print(f"    - {issue['message']}")
                        elif "error" in issue:
                            print(f"    - Error: {issue['error']}")
                    else:
                        print(f"    - {issue}")

        print(f"\nOverall: {'✅ PASS' if results['overall'] else '❌ FAIL'}")

    if args.files and args.generate_tests:
        created_files = support.generate_tests(args.files)
        if created_files:
            print("\nGenerated Test Files:")
            for source_file, test_file in created_files.items():
                print(f"  {source_file} -> {test_file}")
        else:
            print("\nNo test files generated")


if __name__ == "__main__":
    main()
