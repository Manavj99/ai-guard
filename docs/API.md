# AI Guard API Documentation

## Overview

AI Guard provides a comprehensive API for code quality analysis, testing, and security scanning. This document covers the main classes and functions available in the AI Guard library.

## Core Classes

### Gates

The main entry point for AI Guard analysis.

```python
from ai_guard import Gates

gates = Gates()
result = gates.run_analysis("src/")
```

#### Methods

##### `run_analysis(path: str, config: Optional[Dict] = None) -> AnalysisResult`

Runs comprehensive analysis on the specified path.

**Parameters:**
- `path` (str): Path to analyze (file or directory)
- `config` (Optional[Dict]): Configuration dictionary

**Returns:**
- `AnalysisResult`: Analysis results with findings and metrics

**Example:**
```python
result = gates.run_analysis("src/", {
    "min_coverage": 80,
    "security_level": "high"
})
```

##### `run_security_scan(path: str) -> SecurityResult`

Runs security analysis on the specified path.

**Parameters:**
- `path` (str): Path to scan for security issues

**Returns:**
- `SecurityResult`: Security analysis results

##### `run_performance_analysis(path: str) -> PerformanceResult`

Runs performance analysis on the specified path.

**Parameters:**
- `path` (str): Path to analyze for performance issues

**Returns:**
- `PerformanceResult`: Performance analysis results

##### `generate_tests(path: str, target_coverage: int = 80) -> TestGenerationResult`

Generates tests for the specified path.

**Parameters:**
- `path` (str): Path to generate tests for
- `target_coverage` (int): Target test coverage percentage

**Returns:**
- `TestGenerationResult`: Test generation results

## Configuration

### Gates Configuration

```python
config = {
    "gates": {
        "min_coverage": 80,
        "max_complexity": 10,
        "security_level": "high"
    },
    "testing": {
        "parallel_workers": 4,
        "timeout": 300,
        "generate_tests": True
    },
    "performance": {
        "enable_profiling": True,
        "memory_threshold": 100,
        "execution_timeout": 30
    },
    "reports": {
        "format": "sarif",
        "output_path": "ai-guard.sarif",
        "include_performance": True
    }
}
```

### Configuration Options

#### Gates
- `min_coverage` (int): Minimum test coverage percentage (0-100)
- `max_complexity` (int): Maximum cyclomatic complexity
- `security_level` (str): Security level ("low", "medium", "high")

#### Testing
- `parallel_workers` (int): Number of parallel test workers
- `timeout` (int): Test timeout in seconds
- `generate_tests` (bool): Whether to generate tests automatically

#### Performance
- `enable_profiling` (bool): Enable performance profiling
- `memory_threshold` (int): Memory usage threshold in MB
- `execution_timeout` (int): Execution timeout in seconds

#### Reports
- `format` (str): Report format ("sarif", "json", "html")
- `output_path` (str): Output file path
- `include_performance` (bool): Include performance metrics

## Result Objects

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    success: bool
    summary: str
    coverage: float
    issues: List[Issue]
    performance_metrics: Dict[str, Any]
    security_findings: List[SecurityFinding]
```

### SecurityResult

```python
@dataclass
class SecurityResult:
    success: bool
    vulnerabilities: List[Vulnerability]
    dependencies: List[Dependency]
    recommendations: List[str]
```

### PerformanceResult

```python
@dataclass
class PerformanceResult:
    success: bool
    metrics: Dict[str, float]
    bottlenecks: List[Bottleneck]
    recommendations: List[str]
```

### TestGenerationResult

```python
@dataclass
class TestGenerationResult:
    success: bool
    generated_tests: List[str]
    coverage_improvement: float
    test_files: List[str]
```

## Utility Functions

### `summarize(result: AnalysisResult) -> str`

Generates a human-readable summary of analysis results.

**Parameters:**
- `result` (AnalysisResult): Analysis result to summarize

**Returns:**
- `str`: Human-readable summary

**Example:**
```python
from ai_guard import summarize

summary = summarize(result)
print(summary)
```

## Error Handling

AI Guard uses specific exception types for different error conditions:

### `AIGuardError`

Base exception class for all AI Guard errors.

### `ConfigurationError`

Raised when configuration is invalid or missing.

### `AnalysisError`

Raised when analysis fails due to code issues.

### `SecurityError`

Raised when security analysis encounters critical issues.

### `PerformanceError`

Raised when performance analysis fails.

**Example:**
```python
from ai_guard import Gates, AIGuardError

try:
    gates = Gates()
    result = gates.run_analysis("src/")
except AIGuardError as e:
    print(f"AI Guard error: {e}")
```

## CLI Integration

AI Guard can be used from the command line:

```bash
# Basic analysis
ai-guard

# With configuration
ai-guard --config ai-guard.toml

# Specific analysis type
ai-guard --security-only

# Generate report
ai-guard --report-format html --output report.html
```

## Examples

### Basic Usage

```python
from ai_guard import Gates

# Initialize gates
gates = Gates()

# Run analysis
result = gates.run_analysis("src/")

# Check results
if result.success:
    print(f"Analysis passed! Coverage: {result.coverage}%")
else:
    print(f"Analysis failed: {result.summary}")
```

### Advanced Configuration

```python
from ai_guard import Gates

config = {
    "gates": {
        "min_coverage": 90,
        "security_level": "high"
    },
    "testing": {
        "parallel_workers": 8,
        "generate_tests": True
    }
}

gates = Gates(config)
result = gates.run_analysis("src/")
```

### Custom Quality Gates

```python
from ai_guard import Gates, QualityGate

class CustomSecurityGate(QualityGate):
    def check(self, context):
        # Custom security validation logic
        if self.find_vulnerabilities(context.code):
            return GateResult.FAIL, "Security vulnerabilities detected"
        return GateResult.PASS, "Security check passed"

gates = Gates()
gates.add_custom_gate(CustomSecurityGate())
result = gates.run_analysis("src/")
```

## Best Practices

1. **Configuration Management**: Use configuration files for consistent settings across environments.

2. **Error Handling**: Always handle AI Guard exceptions appropriately.

3. **Performance**: Use parallel workers for large codebases.

4. **Security**: Regularly update security rules and dependencies.

5. **Testing**: Generate tests for uncovered code paths.

6. **Monitoring**: Track performance metrics over time.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed correctly.
2. **Configuration Issues**: Validate configuration files with `ai-guard --validate-config`.
3. **Performance Issues**: Reduce parallel workers or increase timeouts.
4. **Security Warnings**: Review and update security rules as needed.

### Getting Help

- 📖 [Documentation](https://ai-guard.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/ai-guard/ai-guard/issues)
- 💬 [Discussions](https://github.com/ai-guard/ai-guard/discussions)
- 📧 [Email Support](mailto:support@ai-guard.dev)
