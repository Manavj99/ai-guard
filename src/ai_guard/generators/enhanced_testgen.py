"""Enhanced test generation with LLM integration and context-aware analysis."""

import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from ..diff_parser import changed_python_files

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestGenConfig:
    """Configuration for test generation."""

    # LLM Configuration
    llm_provider: str = "openai"  # openai, anthropic, local
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-4"  # Default model
    llm_temperature: float = 0.1

    # Test Generation Settings
    test_framework: str = "pytest"  # pytest, unittest
    generate_mocks: bool = True
    generate_parametrized_tests: bool = True
    generate_edge_cases: bool = True
    max_tests_per_file: int = 10

    # Coverage Analysis
    analyze_coverage_gaps: bool = True
    min_coverage_threshold: float = 80.0

    # Output Settings
    output_directory: str = "tests/unit"
    test_file_suffix: str = "_test.py"
    include_docstrings: bool = True
    include_type_hints: bool = True


@dataclass
class CodeChange:
    """Represents a code change for test generation."""

    file_path: str
    function_name: Optional[str]
    class_name: Optional[str]
    change_type: str  # function, class, import, etc.
    line_numbers: Tuple[int, int]
    code_snippet: str
    context: str


@dataclass
class TestGenTemplate:
    """Template for generating tests."""

    name: str
    description: str
    template: str
    variables: List[str]
    applicable_to: List[str]  # function, class, etc.


class EnhancedTestGenerator:
    """Enhanced test generator with LLM integration and context analysis."""

    def __init__(self, config: TestGenConfig):
        self.config = config
        self.test_templates = self._load_test_templates()
        self.llm_client = self._initialize_llm_client()

    def _load_test_templates(self) -> List[TestGenTemplate]:
        """Load built-in test templates."""
        return [
            TestGenTemplate(
                name="function_test",
                description="Basic function test with parameter validation",
                template="""def test_{function_name}():
    \"\"\"Test {function_name} function.\"\"\"
    # Arrange
    {setup_code}

    # Act
    result = {function_name}({test_params})

    # Assert
    {assertions}
""",
                variables=["function_name", "setup_code", "test_params", "assertions"],
                applicable_to=["function"],
            ),
            TestGenTemplate(
                name="function_parametrized_test",
                description="Parametrized function test for multiple scenarios",
                template="""@pytest.mark.parametrize("input_data,expected", [
    {test_cases}
])
def test_{function_name}_parametrized(input_data, expected):
    \"\"\"Test {function_name} with various inputs.\"\"\"
    result = {function_name}(input_data)
    assert result == expected
""",
                variables=["function_name", "test_cases"],
                applicable_to=["function"],
            ),
            TestGenTemplate(
                name="function_error_test",
                description="Error handling and exception testing",
                template="""def test_{function_name}_errors():
    \"\"\"Test {function_name} error handling.\"\"\"
    # Test invalid input types
    with pytest.raises(TypeError):
        {function_name}(None)

    with pytest.raises(ValueError):
        {function_name}("invalid")

    # Test boundary conditions
    with pytest.raises(IndexError):
        {function_name}([])
""",
                variables=["function_name"],
                applicable_to=["function"],
            ),
            TestGenTemplate(
                name="class_test",
                description="Class instantiation and method testing",
                template="""class Test{ClassName}:
    \"\"\"Test {ClassName} class.\"\"\"

    def setup_method(self):
        \"\"\"Set up test fixtures.\"\"\"
        {setup_code}

    def test_instantiation(self):
        \"\"\"Test class instantiation.\"\"\"
        instance = {ClassName}({init_params})
        assert instance is not None
        {assertions}

    def test_methods(self):
        \"\"\"Test class methods.\"\"\"
        instance = {ClassName}({init_params})
        {method_tests}
""",
                variables=[
                    "ClassName",
                    "setup_code",
                    "init_params",
                    "assertions",
                    "method_tests",
                ],
                applicable_to=["class"],
            ),
            TestGenTemplate(
                name="class_property_test",
                description="Class property and attribute testing",
                template="""def test_{class_name}_properties():
    \"\"\"Test {class_name} properties and attributes.\"\"\"
    instance = {class_name}({init_params})

    # Test property access
    {property_tests}

    # Test property modification
    {property_modification_tests}
""",
                variables=[
                    "class_name", "init_params",
                    "property_tests", "property_modification_tests"
                ],
                applicable_to=["class"],
            ),
            TestGenTemplate(
                name="edge_case_test",
                description="Edge case and boundary testing",
                template="""def test_{function_name}_edge_cases():
    \"\"\"Test {function_name} with edge cases.\"\"\"
    # Test with None
    with pytest.raises(ValueError):
        {function_name}(None)

    # Test with empty input
    result = {function_name}("")
    assert result == {expected_empty_result}

    # Test with extreme values
    result = {function_name}({extreme_value})
    assert result == {expected_extreme_result}
""",
                variables=[
                    "function_name",
                    "expected_empty_result",
                    "extreme_value",
                    "expected_extreme_result",
                ],
                applicable_to=["function"],
            ),
            TestGenTemplate(
                name="integration_test",
                description="Integration test with external dependencies",
                template="""@pytest.fixture
def mock_dependencies():
    \"\"\"Mock external dependencies.\"\"\"
    with patch('{module_path}.{dependency}') as mock_dep:
        yield mock_dep

def test_{function_name}_integration(mock_dependencies):
    \"\"\"Test {function_name} integration with dependencies.\"\"\"
    # Setup mock behavior
    mock_dependencies.return_value = {mock_return_value}

    # Test integration
    result = {function_name}({test_params})

    # Verify interactions
    mock_dependencies.assert_called_once_with({expected_args})
    assert result == {expected_result}
""",
                variables=[
                    "function_name",
                    "module_path",
                    "dependency",
                    "mock_return_value",
                    "test_params",
                    "expected_args",
                    "expected_result",
                ],
                applicable_to=["function", "class"],
            ),
            TestGenTemplate(
                name="performance_test",
                description="Performance and timing tests",
                template="""def test_{function_name}_performance():
    \"\"\"Test {function_name} performance characteristics.\"\"\"
    import time

    # Test execution time
    start_time = time.time()
    result = {function_name}({test_params})
    execution_time = time.time() - start_time

    # Assert performance requirements
    assert execution_time < {max_execution_time}  # seconds
    assert result is not None
""",
                variables=["function_name", "test_params", "max_execution_time"],
                applicable_to=["function"],
            ),
            TestGenTemplate(
                name="coverage_test",
                description="Test to improve code coverage",
                template="""def test_{function_name}_coverage():
    \"\"\"Test {function_name} to improve code coverage.\"\"\"
    # Test all code paths
    {coverage_tests}

    # Test with different parameter combinations
    {parameter_combinations}

    # Test return value variations
    {return_value_tests}
""",
                variables=[
                    "function_name", "coverage_tests",
                    "parameter_combinations", "return_value_tests"
                ],
                applicable_to=["function", "class"],
            ),
        ]

    def _initialize_llm_client(self) -> Any:
        """Initialize LLM client based on configuration."""
        if not self.config.llm_api_key:
            logger.warning("No LLM API key provided, using template-based generation")
            return None

        try:
            if self.config.llm_provider == "openai":
                import openai

                openai.api_key = self.config.llm_api_key
                return openai
            elif self.config.llm_provider == "anthropic":
                import anthropic

                return anthropic.Anthropic(api_key=self.config.llm_api_key)
            else:
                logger.warning(f"Unsupported LLM provider: {self.config.llm_provider}")
                return None
        except ImportError as e:
            logger.warning(f"LLM library not available: {e}")
            return None

    def analyze_code_changes(
        self, changed_files: List[str], event_path: Optional[str] = None
    ) -> List[CodeChange]:
        """Analyze code changes to understand what needs testing."""
        changes: List[CodeChange] = []

        for file_path in changed_files:
            if not file_path.endswith(".py"):
                continue

            try:
                file_changes = self._analyze_file_changes(file_path, event_path)
                changes.extend(file_changes)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")

        return changes

    def _analyze_file_changes(
        self, file_path: str, event_path: Optional[str] = None
    ) -> List[CodeChange]:
        """Analyze changes in a specific file."""
        changes: List[CodeChange] = []

        try:
            # Get the actual diff content
            diff_content = self._get_file_diff(file_path, event_path)
            if not diff_content:
                return changes

            # Parse the Python file to understand structure
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    logger.warning(f"Syntax error in {file_path}, skipping")
                    return changes

            # Analyze the diff to find changed functions/classes
            changed_lines = self._parse_diff_lines(diff_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if self._is_function_changed(node, changed_lines):
                        changes.append(
                            CodeChange(
                                file_path=file_path,
                                function_name=node.name,
                                class_name=self._get_class_name(node),
                                change_type="function",
                                line_numbers=(
                                    node.lineno,
                                    node.end_lineno or node.lineno,
                                ),
                                code_snippet=ast.unparse(node),
                                context=self._get_function_context(node),
                            )
                        )
                elif isinstance(node, ast.ClassDef):
                    if self._is_class_changed(node, changed_lines):
                        changes.append(
                            CodeChange(
                                file_path=file_path,
                                function_name=None,
                                class_name=node.name,
                                change_type="class",
                                line_numbers=(
                                    node.lineno,
                                    node.end_lineno or node.lineno,
                                ),
                                code_snippet=ast.unparse(node),
                                context=self._get_class_context(node),
                            )
                        )

        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")

        return changes

    def _get_file_diff(
        self, file_path: str, event_path: Optional[str] = None
    ) -> Optional[str]:
        """Get the diff content for a specific file."""
        try:
            if event_path:
                # Try to get diff from GitHub event
                base_head = self._get_base_head_from_event(event_path)
                if base_head:
                    base, head = base_head
                    result = subprocess.run(
                        ["git", "diff", f"{base}...{head}", "--", file_path],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0:
                        return result.stdout
        except Exception as e:
            logger.debug(f"Could not get diff from event: {e}")

        # Fallback: get diff from working directory
        try:
            result = subprocess.run(
                ["git", "diff", "--", file_path],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            logger.debug(f"Could not get git diff: {e}")

        return None

    def _get_base_head_from_event(self, event_path: str) -> Optional[Tuple[str, str]]:
        """Extract base and head from GitHub event."""
        try:
            with open(event_path, "r") as f:
                event = json.load(f)

            if "pull_request" in event:
                pr = event["pull_request"]
                return pr["base"]["sha"], pr["head"]["sha"]
            elif "before" in event and "after" in event:
                return event["before"], event["after"]
        except Exception as e:
            logger.debug(f"Error parsing event: {e}")

        return None

    def _parse_diff_lines(self, diff_content: str) -> List[int]:
        """Parse diff content to extract changed line numbers."""
        changed_lines = []

        for line in diff_content.split("\n"):
            if line.startswith("@@"):
                # Parse @@ -old_start,old_count +new_start,new_count @@
                match = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if match:
                    start_line = int(match.group(1))
                    # Add a few lines for context
                    for i in range(max(1, start_line - 2), start_line + 10):
                        changed_lines.append(i)

        return changed_lines

    def _is_function_changed(
        self, node: ast.FunctionDef, changed_lines: List[int]
    ) -> bool:
        """Check if a function was changed based on line numbers."""
        return any(
            line in changed_lines
            for line in range(node.lineno, (node.end_lineno or node.lineno) + 1)
        )

    def _is_class_changed(self, node: ast.ClassDef, changed_lines: List[int]) -> bool:
        """Check if a class was changed based on line numbers."""
        return any(
            line in changed_lines
            for line in range(node.lineno, (node.end_lineno or node.lineno) + 1)
        )

    def _get_class_name(self, node: ast.FunctionDef) -> Optional[str]:
        """Get the class name if the function is inside a class."""
        parent = getattr(node, "parent", None)
        while parent:
            if isinstance(parent, ast.ClassDef):
                return parent.name
            parent = getattr(parent, "parent", None)
        return None

    def _get_function_context(self, node: ast.FunctionDef) -> str:
        """Get context information about a function."""
        context_parts = []

        # Get decorators
        if node.decorator_list:
            decorators = [ast.unparse(d) for d in node.decorator_list]
            context_parts.append(f"Decorators: {', '.join(decorators)}")

        # Get arguments
        args = [arg.arg for arg in node.args.args]
        if args:
            context_parts.append(f"Arguments: {', '.join(args)}")

        # Get return annotation
        if node.returns:
            context_parts.append(f"Returns: {ast.unparse(node.returns)}")

        return "; ".join(context_parts)

    def _get_class_context(self, node: ast.ClassDef) -> str:
        """Get context information about a class."""
        context_parts = []

        # Get base classes
        if node.bases:
            bases = [ast.unparse(b) for b in node.bases]
            context_parts.append(f"Bases: {', '.join(bases)}")

        # Get methods
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        if methods:
            context_parts.append(f"Methods: {', '.join(methods)}")

        return "; ".join(context_parts)

    def generate_tests_with_llm(self, code_change: CodeChange) -> str:
        """Generate tests using LLM if available."""
        if not self.llm_client:
            return self._generate_tests_with_templates(code_change)

        try:
            prompt = self._create_llm_prompt(code_change)

            if self.config.llm_provider == "openai":
                response = self.llm_client.ChatCompletion.create(
                    model=self.config.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.config.llm_temperature,
                    max_tokens=1000,
                )
                content = response.choices[0].message.content
                if isinstance(content, str):
                    return content
                return ""
            elif self.config.llm_provider == "anthropic":
                response = self.llm_client.messages.create(
                    model=self.config.llm_model,
                    max_tokens=1000,
                    temperature=self.config.llm_temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.content[0].text
                if isinstance(content, str):
                    return content
                return ""

        except Exception as e:
            logger.warning(f"LLM generation failed: {e}, falling back to templates")

        return self._generate_tests_with_templates(code_change)

    def _create_llm_prompt(self, code_change: CodeChange) -> str:
        """Create a prompt for LLM test generation."""
        return f"""Generate comprehensive tests for the following Python code change:

File: {code_change.file_path}
Type: {code_change.change_type}
Name: {code_change.function_name or code_change.class_name}
Context: {code_change.context}

Code:
{code_change.code_snippet}

Requirements:
1. Use pytest framework
2. Include proper docstrings
3. Test both happy path and edge cases
4. Use descriptive test names
5. Include parameterized tests where appropriate
6. Mock external dependencies if needed
7. Test error conditions and exceptions
8. Ensure good test coverage

Generate only the test code, no explanations or markdown formatting."""

    def _generate_tests_with_templates(self, code_change: CodeChange) -> str:
        """Generate tests using built-in templates."""
        if code_change.change_type == "function":
            return self._generate_function_tests(code_change)
        elif code_change.change_type == "class":
            return self._generate_class_tests(code_change)
        else:
            return self._generate_generic_tests(code_change)

    def _generate_function_tests(self, code_change: CodeChange) -> str:
        """Generate tests for a function using templates."""
        tests = []

        # Extract function signature information
        try:
            tree = ast.parse(code_change.code_snippet)
            func_def = next(
                (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)), None
            )

            if func_def:
                args = [arg.arg for arg in func_def.args.args]

                # Generate basic function test
                basic_template = next(
                    (t for t in self.test_templates if t.name == "function_test"), None
                )
                if basic_template:
                    test_params = ", ".join(
                        [f'"{arg}"' if isinstance(arg, str) else str(arg) for arg in args[:2]]
                    )
                    setup_code = f"# Setup test data for {code_change.function_name}"
                    assertions = (
                        "assert result is not None\n    "
                        "assert isinstance(result, (str, int, float, bool))"
                    )

                    tests.append(basic_template.template.format(
                        function_name=code_change.function_name,
                        setup_code=setup_code,
                        test_params=test_params,
                        assertions=assertions,
                    ))

                # Generate parametrized test if function has multiple parameters
                if len(args) > 1:
                    parametrized_template = next(
                        (t for t in self.test_templates if t.name == "function_parametrized_test"), None
                    )
                    if parametrized_template:
                        test_cases = self._generate_test_cases(func_def)
                        tests.append(parametrized_template.template.format(
                            function_name=code_change.function_name,
                            test_cases=test_cases,
                        ))

                # Generate error handling test
                error_template = next(
                    (t for t in self.test_templates if t.name == "function_error_test"), None
                )
                if error_template:
                    tests.append(error_template.template.format(
                        function_name=code_change.function_name,
                    ))

                # Generate edge case test
                edge_template = next(
                    (t for t in self.test_templates if t.name == "edge_case_test"), None
                )
                if edge_template:
                    tests.append(edge_template.template.format(
                        function_name=code_change.function_name,
                        expected_empty_result="None",
                        extreme_value="float('inf')",
                        expected_extreme_result="None",
                    ))

                # Generate coverage test
                coverage_template = next(
                    (t for t in self.test_templates if t.name == "coverage_test"), None
                )
                if coverage_template:
                    coverage_tests = self._generate_coverage_tests(func_def)
                    tests.append(coverage_template.template.format(
                        function_name=code_change.function_name,
                        coverage_tests=coverage_tests,
                        parameter_combinations="# Add parameter combinations here",
                        return_value_tests="# Add return value tests here",
                    ))

        except Exception as e:
            logger.debug(f"Error parsing function: {e}")

        if not tests:
            return self._generate_generic_tests(code_change)

        return "\n\n".join(tests)

    def _generate_test_cases(self, func_def: ast.FunctionDef) -> str:
        """Generate test cases for parametrized tests."""
        args = [arg.arg for arg in func_def.args.args]
        test_cases = []

        # Generate basic test cases
        if len(args) >= 1:
            test_cases.append('    ("test_input", "expected_output"),')
            test_cases.append('    ("", ""),')
            test_cases.append('    (None, None),')

        if len(args) >= 2:
            test_cases.append('    (("arg1", "arg2"), "expected_output"),')

        return "\n".join(test_cases)

    def _generate_coverage_tests(self, func_def: ast.FunctionDef) -> str:
        """Generate coverage-specific tests."""
        coverage_tests = []

        # Test with different input types
        coverage_tests.append("    # Test with different input types")
        coverage_tests.append("    result = {function_name}(1)")
        coverage_tests.append("    assert result is not None")

        # Test with different parameter combinations
        args = [arg.arg for arg in func_def.args.args]
        if len(args) > 1:
            coverage_tests.append("    # Test with multiple parameters")
            coverage_tests.append("    result = {function_name}(1, 2)")
            coverage_tests.append("    assert result is not None")

        return "\n".join(coverage_tests).format(function_name=func_def.name)

    def _generate_class_tests(self, code_change: CodeChange) -> str:
        """Generate tests for a class using templates."""
        template = next(
            (t for t in self.test_templates if "class" in t.applicable_to), None
        )
        if not template:
            return self._generate_generic_tests(code_change)

        return template.template.format(
            ClassName=code_change.class_name,
            setup_code="# Initialize test data",
            init_params="",
            assertions="assert isinstance(instance, type(instance))",
            method_tests="# Add method tests here",
        )

    def _generate_generic_tests(self, code_change: CodeChange) -> str:
        """Generate generic tests when templates don't apply."""
        change_name = code_change.function_name or code_change.class_name
        return f'''def test_{code_change.change_type}_{change_name}():
    """Test {code_change.change_type} {change_name}."""
    # TODO: Implement specific tests based on code analysis
    assert True

def test_{code_change.change_type}_{change_name}_import():
    """Test that {code_change.change_type} can be imported."""
    # This test ensures the changed code is syntactically valid
    assert True
'''

    def analyze_coverage_gaps(self, changed_files: List[str]) -> Dict[str, List[str]]:
        """Analyze coverage gaps and suggest specific tests."""
        if not self.config.analyze_coverage_gaps:
            return {}

        coverage_gaps = {}

        for file_path in changed_files:
            if not file_path.endswith(".py"):
                continue

            try:
                gaps = self._analyze_file_coverage(file_path)
                if gaps:
                    coverage_gaps[file_path] = gaps
            except Exception as e:
                logger.warning(f"Error analyzing coverage for {file_path}: {e}")

        return coverage_gaps

    def _analyze_file_coverage(self, file_path: str) -> List[str]:
        """Analyze coverage gaps in a specific file."""
        gaps = []

        try:
            # Run coverage on the file
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "coverage",
                    "run",
                    "--source",
                    file_path,
                    "-m",
                    "pytest",
                    file_path,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                # Parse coverage report
                coverage_result = subprocess.run(
                    ["python", "-m", "coverage", "report", "--show-missing"],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if coverage_result.returncode == 0:
                    lines = coverage_result.stdout.split("\n")
                    for line in lines:
                        if "Missing" in line and file_path in line:
                            # Extract missing line numbers
                            missing_match = re.search(r"Missing: (.+)", line)
                            if missing_match:
                                missing_lines = missing_match.group(1)
                                gaps.append(
                                    f"Lines {missing_lines} are not covered by tests"
                                )

                # Also analyze coverage by function/class
                function_gaps = self._analyze_function_coverage(file_path)
                gaps.extend(function_gaps)

                # Analyze branch coverage
                branch_gaps = self._analyze_branch_coverage(file_path)
                gaps.extend(branch_gaps)

        except Exception as e:
            logger.debug(f"Error running coverage analysis: {e}")

        return gaps

    def _analyze_function_coverage(self, file_path: str) -> List[str]:
        """Analyze function-level coverage gaps."""
        gaps = []

        try:
            # Parse the Python file to find functions
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function has docstring but no tests
                    if (node.body
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)):
                        gaps.append(
                            f"Function '{node.name}' has docstring but may lack comprehensive tests")

                    # Check for complex functions that might need more testing
                    if len(node.body) > 10:  # Arbitrary threshold for complexity
                        gaps.append(
                            f"Function '{node.name}' is complex and may need additional test cases")

        except Exception as e:
            logger.debug(f"Error analyzing function coverage: {e}")

        return gaps

    def _analyze_branch_coverage(self, file_path: str) -> List[str]:
        """Analyze branch coverage gaps."""
        gaps = []

        try:
            # Parse the Python file to find conditional statements
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    gaps.append(
                        f"Conditional statement at line {node.lineno} may need both True/False branch tests")
                elif isinstance(node, ast.For):
                    gaps.append(
                        f"Loop at line {node.lineno} may need empty list and non-empty list tests")
                elif isinstance(node, ast.While):
                    gaps.append(
                        f"While loop at line {node.lineno} may need boundary condition tests")
                elif isinstance(node, ast.Try):
                    gaps.append(
                        f"Try-except block at line {node.lineno} may need exception path tests")

        except Exception as e:
            logger.debug(f"Error analyzing branch coverage: {e}")

        return gaps

    def generate_test_file(
        self, code_changes: List[CodeChange], output_path: str
    ) -> str:
        """Generate a complete test file with all generated tests."""
        if not code_changes:
            return ""

        # Group changes by file
        changes_by_file: Dict[str, List[CodeChange]] = {}
        for change in code_changes:
            if change.file_path not in changes_by_file:
                changes_by_file[change.file_path] = []
            changes_by_file[change.file_path].append(change)

        # Generate test content
        test_content = [
            "# Auto-generated tests using AI-Guard Enhanced Test Generator",
            "# Generated for the following changed files:",
            "",
        ]

        for file_path in changes_by_file:
            test_content.append(f"# - {file_path}")

        test_content.extend(
            [
                "",
                "import pytest",
                "from unittest.mock import Mock, patch",
                "",
                "# Test imports",
                "try:",
            ]
        )

        # Add import statements for changed files
        for file_path in changes_by_file:
            module_path = file_path.replace("/", ".").replace(".py", "")
            test_content.append(f"    from {module_path} import *")

        test_content.extend(
            [
                "except ImportError:",
                "    pass  # Tests will fail if imports don't work",
                "",
                "",
            ]
        )

        # Generate tests for each change
        for file_path, changes in changes_by_file.items():
            test_content.append(f"# Tests for {file_path}")
            test_content.append("")

            for change in changes:
                test_content.append(self.generate_tests_with_llm(change))
                test_content.append("")

        # Add coverage gap suggestions
        coverage_gaps = self.analyze_coverage_gaps([c.file_path for c in code_changes])
        if coverage_gaps:
            test_content.append("# Coverage Gap Analysis")
            test_content.append("")
            for file_path, gaps in coverage_gaps.items():
                test_content.append(f"# {file_path}:")
                for gap in gaps:
                    test_content.append(f"# - {gap}")
                test_content.append("")

        return "\n".join(test_content)

    def generate_tests(
        self,
        changed_files: List[str],
        event_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """Main method to generate tests for changed files."""
        if not changed_files:
            logger.info("No files changed, skipping test generation")
            return ""

        # Analyze code changes
        logger.info(f"Analyzing changes in {len(changed_files)} files...")
        code_changes = self.analyze_code_changes(changed_files, event_path)

        if not code_changes:
            logger.info("No code changes detected that require testing")
            return ""

        logger.info(f"Detected {len(code_changes)} code changes requiring tests")

        # Generate test content
        test_content = self.generate_test_file(
            code_changes, output_path or "tests/unit/test_generated.py"
        )

        return test_content


def main() -> None:
    """Main entry point for enhanced test generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced test generation with LLM integration"
    )
    parser.add_argument("--event", help="Path to GitHub event JSON file")
    parser.add_argument(
        "--output",
        default="tests/unit/test_generated.py",
        help="Output path for generated tests",
    )
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "anthropic", "local"],
        default="openai",
        help="LLM provider to use",
    )
    parser.add_argument("--llm-api-key", help="API key for LLM provider")
    parser.add_argument("--llm-model", default="gpt-4", help="LLM model to use")

    args = parser.parse_args()

    # Load configuration
    config = TestGenerationConfig(
        llm_provider=args.llm_provider,
        llm_api_key=args.llm_api_key
        or os.getenv(f"{args.llm_provider.upper()}_API_KEY"),
        llm_model=args.llm_model,
    )

    # Initialize generator
    generator = EnhancedTestGenerator(config)

    # Get changed files
    changed_files = changed_python_files(args.event)

    if not changed_files:
        print("[enhanced-testgen] No Python files changed, skipping test generation")
        return

    # Generate tests
    test_content = generator.generate_tests(changed_files, args.event, args.output)

    if test_content:
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write generated tests
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(test_content)

        print(
            f"[enhanced-testgen] Generated enhanced tests for {len(changed_files)} files"
        )
        print(f"[enhanced-testgen] Output: {output_path}")
    else:
        print("[enhanced-testgen] No tests generated")


# Aliases for backward compatibility
TestGenerationConfig = TestGenConfig
TestTemplate = TestGenTemplate

if __name__ == "__main__":
    main()
