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
