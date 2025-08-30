# AI-Guard: Smart Code Quality Gatekeeper

**Goal:** Stop risky PRs (especially AI-generated ones) from merging by enforcing quality, security, and test gates — and by auto-generating targeted tests for changed code.

[![AI-Guard Workflow](https://github.com/Manavj99/ai-guard/workflows/AI-Guard/badge.svg)](https://github.com/Manavj99/ai-guard/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)](https://github.com/Manavj99/ai-guard)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Why AI-Guard?

Modern teams ship faster with AI. AI-Guard keeps quality high with automated, opinionated gates: lint, types, security, coverage, and speculative tests.

## ✨ Features

- **🔍 Quality Gates**: Linting (flake8), typing (mypy), security scan (bandit)
- **📊 Coverage Enforcement**: Configurable coverage thresholds (default: 80%)
- **🛡️ Security Scanning**: Automated vulnerability detection with Bandit
- **🧪 Test Generation**: Speculative test generation for changed files
- **📋 SARIF Output**: GitHub Code Scanning compatible results
- **⚡ CI Integration**: Single-command GitHub Actions integration
- **🎛️ Configurable**: Easy customization via TOML configuration

## 🚀 Quickstart

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

Generate SARIF output for GitHub Code Scanning:

```bash
python -m src.ai_guard check --min-cov 80 --skip-tests --sarif ai-guard.sarif
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
  --min-cov INTEGER     Override min coverage % [default: 80]
  --skip-tests         Skip running tests (useful for CI)
  --event PATH         Path to GitHub event JSON
  --sarif PATH         Output SARIF path [default: ai-guard.sarif]
  --help               Show this message and exit
```

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

### SARIF Output

AI-Guard generates SARIF files compatible with GitHub Code Scanning:

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

### Workflow Status

- ✅ **Green**: All quality gates passed
- ❌ **Red**: One or more quality gates failed
- 🟡 **Yellow**: Workflow in progress

## 📊 Current Status

- **Test Coverage**: 87% (364 statements, 48 missing)
- **Quality Gates**: All passing ✅
- **Security Scan**: Bandit integration active
- **SARIF Output**: GitHub Code Scanning compatible
- **GitHub Actions**: Fully configured and tested

## 🏗️ Project Structure

```
ai-guard/
├── src/ai_guard/           # Core package
│   ├── analyzer.py         # Main quality gate orchestrator
│   ├── config.py           # Configuration management
│   ├── diff_parser.py      # Git diff parsing
│   ├── sarif_report.py     # SARIF output generation
│   ├── security_scanner.py # Security scanning
│   └── tests_runner.py     # Test execution
├── tests/                  # Test suite
├── .github/workflows/      # GitHub Actions
├── ai-guard.toml          # Configuration
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
- [ ] LLM-assisted test synthesis (opt-in)
- [ ] Language adapters (JS/TS, Go, Rust)
- [ ] Advanced PR annotations
- [ ] Custom rule engine

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Manavj99/ai-guard/issues)
- **Security**: [SECURITY.md](SECURITY.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Made with ❤️ for better code quality** 
