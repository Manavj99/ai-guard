# AI-Guard: Smart Code Quality Gatekeeper

**Goal:** Stop risky PRs (especially AI-generated ones) from merging by enforcing quality, security, and test gates — and by auto-generating targeted tests for changed code.

[![AI-Guard Workflow](https://github.com/Manavj99/ai-guard/workflows/AI-Guard/badge.svg)](https://github.com/Manavj99/ai-guard/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-83%25-brightgreen)](https://github.com/Manavj99/ai-guard)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Why AI-Guard?

Modern teams ship faster with AI. AI-Guard keeps quality high with automated, opinionated gates: lint, types, security, coverage, and speculative tests.

## ✨ Features

- **🔍 Quality Gates**: Linting (flake8), typing (mypy), security scan (bandit)
- **📊 Coverage Enforcement**: Configurable coverage thresholds (default: 80%)
- **🛡️ Security Scanning**: Automated vulnerability detection with Bandit
- **🧪 Test Generation**: Speculative test generation for changed files
- **🤖 Enhanced Test Generation**: LLM-powered, context-aware test generation with OpenAI/Anthropic
- **🌐 Multi-Language Support**: JavaScript/TypeScript support with ESLint, Prettier, Jest
- **📝 PR Annotations**: Advanced GitHub integration with inline comments and review summaries
- **📋 Multi-Format Reports**: SARIF (GitHub Code Scanning), JSON (CI automation), HTML (artifacts)
- **⚡ Performance Optimized**: Parallel execution, caching, and performance monitoring
- **🚀 Fast Execution**: Up to 54% faster with optimized subprocess handling and caching
- **📈 Performance Monitoring**: Built-in performance metrics and reporting
- **⚡ CI Integration**: Single-command GitHub Actions integration
- **🎛️ Configurable**: Easy customization via TOML configuration

## 🚀 Quickstart

### Enhanced Features

AI-Guard now includes several enhanced features for better development experience:

- **🤖 Enhanced Test Generation**: Use LLMs (OpenAI GPT-4, Anthropic Claude) to generate intelligent, context-aware tests
- **🌐 JavaScript/TypeScript Support**: Quality gates for JS/TS projects with ESLint, Prettier, Jest, and TypeScript
- **📝 PR Annotations**: Generate comprehensive PR reviews with inline comments and suggestions
- **⚡ Performance Optimizations**: Parallel execution, intelligent caching, and performance monitoring

See [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md) for detailed documentation.

### Performance Features

AI-Guard includes advanced performance optimizations:

- **🚀 Parallel Execution**: Run quality checks concurrently for up to 54% faster execution
- **💾 Intelligent Caching**: Cache results for repeated operations (coverage parsing, config loading)
- **📊 Performance Monitoring**: Built-in metrics tracking and reporting
- **⏱️ Timeout Handling**: Robust subprocess management with configurable timeouts
- **🔧 Optimized Subprocess**: Enhanced subprocess handling with better error management

Use the optimized analyzer for maximum performance:

```bash
# Use optimized analyzer with parallel execution
python -m src.ai_guard.analyzer_optimized --parallel --performance-report

# Compare performance between versions
python performance_comparison.py
```

### Installation

```bash
# Clone the repository
git clone https://github.com/Manavj99/ai-guard.git
cd ai-guard

# Install dependencies
pip install -r requirements.txt

# Run tests to verify installation
pytest -q
```

### Basic Usage

Run quality checks with default settings:

```bash
python -m src.ai_guard check
```

Run with custom coverage threshold:

```bash
python -m src.ai_guard check --min-cov 90 --skip-tests
```

Run with enhanced test generation and PR annotations:

```bash
# Enhanced test generation with OpenAI
python -m src.ai_guard.analyzer \
  --enhanced-testgen \
  --llm-provider openai \
  --pr-annotations \
  --event "$GITHUB_EVENT_PATH"

# JavaScript/TypeScript quality checks
python -m src.ai_guard.language_support.js_ts_support \
  --quality \
  --files src/**/*.js src/**/*.ts
```

Generate different report formats:

```bash
# SARIF for GitHub Code Scanning (default)
python -m src.ai_guard check --min-cov 80 --skip-tests --sarif ai-guard.sarif

# JSON for CI automation
python -m src.ai_guard check --min-cov 80 --skip-tests --report-format json

# HTML for CI artifacts
python -m src.ai_guard check --min-cov 80 --skip-tests --report-format html

# Custom report path
python -m src.ai_guard check --min-cov 80 --skip-tests --report-format html --report-path reports/quality.html
```

### Using Docker

Build the Docker image:

```bash
# Build image
make docker
# or manually:
docker build -t ai-guard:latest .
```

Run quality checks in Docker:

```bash
# Full scan with tests & SARIF
docker run --rm -v "$PWD":/workspace ai-guard:latest \
  --min-cov 85 \
  --sarif /workspace/ai-guard.sarif

# Quick scan (no tests) on the repo
docker run --rm -v "$PWD":/workspace ai-guard:latest \
  --skip-tests \
  --sarif /workspace/ai-guard.sarif

# Using make target
make docker-run
```

**Why Docker?**
- **Reproducible**: Exact Python + toolchain versions
- **Portable**: Works the same everywhere (laptop, CI, cloud)
- **Secure**: Non-root user, minimal base image
- **Fast**: Only changed files get type/lint checks with `--event`

## ⚙️ Configuration

Create an `ai-guard.toml` file in your project root:

```toml
[gates]
min_coverage = 80
```

## 🔧 CLI Options

```bash
python -m src.ai_guard check [OPTIONS]

Options:
  --min-cov INTEGER           Override min coverage % [default: 80]
  --skip-tests               Skip running tests (useful for CI)
  --event PATH               Path to GitHub event JSON
  --report-format FORMAT     Output format: sarif, json, or html [default: sarif]
  --report-path PATH         Path to write the report (default depends on format)
  --sarif PATH               (Deprecated) Output SARIF path; use --report-format/--report-path
  --performance-report       Generate performance metrics report
  --help                     Show this message and exit
```

### Optimized Analyzer Options

```bash
python -m src.ai_guard.analyzer_optimized [OPTIONS]

Additional Options:
  --parallel                 Enable parallel execution of quality checks
  --performance-report       Generate detailed performance metrics
```

**Report Formats:**
- **`sarif`**: GitHub Code Scanning compatible SARIF output (default)
- **`json`**: Machine-readable JSON summary with gate results and findings
- **`html`**: Human-friendly HTML report for CI artifacts and dashboards

**Default Report Paths:**
- `sarif`: `ai-guard.sarif`
- `json`: `ai-guard.json`  
- `html`: `ai-guard.html`

## 📋 Example Outputs

### Console Output

**Passing run:**
```
Changed Python files: ['src/foo/utils.py']
Lint (flake8): PASS
Static types (mypy): PASS
Security (bandit): PASS (0 high findings)
Coverage: PASS (86% ≥ min 85%)
Summary: all gates passed ✅
```

**Failing run:**
```
Changed Python files: ['src/foo/handler.py']
Lint (flake8): PASS
Static types (mypy): FAIL
  src/foo/handler.py:42: error: Argument 1 to "process" has incompatible type "str"; expected "int"  [arg-type]
Security (bandit): PASS (0 high findings)
Coverage: FAIL (78% < min 85%)

Summary:
✗ Static types (mypy)
✗ Coverage (min 85%)
Exit code: 1
```

### Report Outputs

AI-Guard supports multiple output formats for different use cases:

#### SARIF Output (Default)

GitHub Code Scanning compatible SARIF files:

```json
{
  "version": "2.1.0",
  "runs": [
    {
      "tool": { "driver": { "name": "AI-Guard", "version": "0.1.0" } },
      "results": [
        {
          "ruleId": "mypy:arg-type",
          "level": "error",
          "message": { "text": "Argument 1 to 'process' has incompatible type 'str'; expected 'int'" },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": { "uri": "src/foo/handler.py" },
                "region": { "startLine": 42 }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

#### JSON Output

Machine-readable summary for CI ingestion and automation:

```json
{
  "version": "1.0",
  "summary": {
    "passed": false,
    "gates": [
      {"name": "Lint (flake8)", "passed": true, "details": ""},
      {"name": "Static types (mypy)", "passed": false, "details": "mypy not found"},
      {"name": "Coverage", "passed": true, "details": "85% >= 80%"}
    ]
  },
  "findings": [
    {
      "rule_id": "mypy:arg-type",
      "level": "error", 
      "message": "Argument 1 to 'process' has incompatible type",
      "path": "src/foo/handler.py",
      "line": 42
    }
  ]
}
```

#### HTML Output

Human-friendly report for CI artifacts and dashboards:

```bash
# Generate HTML report
ai-guard --report-format html --report-path ai-guard.html --min-cov 85

# Upload as CI artifact (GitHub Actions example)
- name: Upload HTML report
  uses: actions/upload-artifact@v4
  with:
    name: ai-guard-report
    path: ai-guard.html
```

## 🐙 GitHub Integration

### Automatic PR Checks

AI-Guard automatically runs on every Pull Request to `main` or `master` branches:

1. **Linting**: Enforces flake8 standards
2. **Type Checking**: Runs mypy for static type validation
3. **Security Scan**: Executes Bandit security analysis
4. **Test Coverage**: Ensures minimum coverage threshold
5. **Quality Gates**: Comprehensive quality assessment
6. **SARIF Upload**: Results integrated with GitHub Code Scanning

### Manual Workflow Trigger

You can manually trigger the workflow from the GitHub Actions tab:

1. Go to **Actions** → **AI-Guard**
2. Click **Run workflow**
3. Select branch and click **Run workflow**

### Using Docker in GitHub Actions

If you prefer containerized jobs, you can use the Docker image:

```yaml
name: AI-Guard
on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build AI-Guard image
        run: docker build -t ai-guard:latest .

      # Pass the GitHub event JSON so AI-Guard scopes to changed files
      - name: Run AI-Guard
        run: |
          docker run --rm \
            -v "$GITHUB_WORKSPACE":/workspace \
            -v "$GITHUB_EVENT_PATH":/tmp/event.json:ro \
            ai-guard:latest \
              --event /tmp/event.json \
              --min-cov 85 \
              --sarif /workspace/ai-guard.sarif

      # Surface SARIF in the Security tab
      - name: Upload SARIF to code scanning
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: ai-guard.sarif
```

This will fail the job (and block the PR) if any gate fails, and the SARIF will appear in **Security → Code scanning alerts**.

### Multi-Format Reporting in CI

AI-Guard supports multiple output formats for different CI needs:

#### JSON Reports for Automation

Generate machine-readable reports for CI decision making:

```yaml
- name: Run AI-Guard (JSON)
  run: |
    python -m src.ai_guard.analyzer \
      --report-format json \
      --report-path ai-guard.json \
      --min-cov 85 \
      --skip-tests

- name: Parse results for CI logic
  run: |
    if python -c "import json; data=json.load(open('ai-guard.json')); exit(0 if data['summary']['passed'] else 1)"; then
      echo "All gates passed"
    else
      echo "Some gates failed"
      exit 1
    fi
```

#### HTML Reports for Artifacts

Generate human-friendly reports for CI artifacts:

```yaml
- name: Run AI-Guard (HTML)
  run: |
    python -m src.ai_guard.analyzer \
      --report-format html \
      --report-path ai-guard.html \
      --min-cov 85 \
      --skip-tests

- name: Upload HTML report artifact
  uses: actions/upload-artifact@v4
  with:
    name: ai-guard-report
    path: ai-guard.html
    retention-days: 30
```

#### Combined Workflow Example

Run multiple formats in a single workflow:

```yaml
- name: Run AI-Guard (All formats)
  run: |
    python -m src.ai_guard.analyzer \
      --report-format sarif \
      --report-path ai-guard.sarif \
      --min-cov 85 \
      --skip-tests
    
    python -m src.ai_guard.analyzer \
      --report-format json \
      --report-path ai-guard.json \
      --min-cov 85 \
      --skip-tests
    
    python -m src.ai_guard.analyzer \
      --report-format html \
      --report-path ai-guard.html \
      --min-cov 85 \
      --skip-tests

- name: Upload all reports
  uses: actions/upload-artifact@v4
  with:
    name: ai-guard-reports
    path: |
      ai-guard.sarif
      ai-guard.json
      ai-guard.html
```

### Workflow Status

- ✅ **Green**: All quality gates passed
- ❌ **Red**: One or more quality gates failed
- 🟡 **Yellow**: Workflow in progress

## 📊 Current Status

- **Test Coverage**: 83% (518 statements, 76 missing) - Core analyzer module
- **Quality Gates**: All passing ✅ (140 tests passed)
- **Security Scan**: Bandit integration active
- **SARIF Output**: GitHub Code Scanning compatible
- **GitHub Actions**: Fully configured and tested
- **Recent Improvements**: Enhanced test coverage, error handling, and reliability

## 🏗️ Project Structure

```
ai-guard/
├── src/ai_guard/           # Core package
│   ├── analyzer.py         # Main quality gate orchestrator
│   ├── analyzer_optimized.py # Optimized analyzer with performance features
│   ├── config.py           # Configuration management
│   ├── diff_parser.py      # Git diff parsing
│   ├── performance.py      # Performance monitoring and optimization utilities
│   ├── report.py           # Core reporting and result aggregation
│   ├── report_json.py      # JSON report generation
│   ├── report_html.py      # HTML report generation
│   ├── sarif_report.py     # SARIF output generation
│   ├── security_scanner.py # Security scanning
│   └── tests_runner.py     # Test execution
├── tests/                  # Test suite
├── .github/workflows/      # GitHub Actions
├── ai-guard.toml          # Configuration
├── performance_comparison.py # Performance benchmarking script
└── requirements.txt        # Dependencies
```

## 🧪 Testing

Run the complete test suite:

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test modules
pytest tests/unit/test_analyzer.py -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

## 🔒 Security

- **Bandit Integration**: Automated security vulnerability scanning
- **Dependency Audit**: pip-audit for known vulnerabilities
- **SARIF Security Events**: GitHub Code Scanning integration
- **Configurable Severity**: Adjustable security thresholds

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run quality checks
make check

# Run tests
make test
```

## 📈 Roadmap

- [x] Parse PR diffs to target functions precisely
- [x] SARIF output + GitHub Code Scanning integration
- [x] Comprehensive quality gates
- [x] Performance optimizations and monitoring
- [x] Parallel execution and intelligent caching
- [x] LLM-assisted test synthesis (opt-in)
- [x] Language adapters (JS/TS support)
- [x] Advanced PR annotations
- [ ] Additional language adapters (Go, Rust)
- [ ] Custom rule engine
- [ ] Distributed execution
- [ ] Machine learning-based optimization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Manavj99/ai-guard/issues)
- **Security**: [SECURITY.md](SECURITY.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Made with ❤️ for better code quality** 
