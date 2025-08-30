# AI-Guard Test Project

This is a test project to verify that AI-Guard works correctly in CI/CD pipelines and can be properly installed and used.

## 🎯 Purpose

This project serves as a comprehensive test suite for AI-Guard, demonstrating:
- Installation and setup
- Integration with CI/CD pipelines
- Quality gate enforcement
- Test generation capabilities
- Reporting and monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git
- Access to AI-Guard package

### Installation

1. **Clone the test project:**
   ```bash
   git clone <your-repo-url>/test-project.git
   cd test-project
   ```

2. **Install AI-Guard:**
   ```bash
   # From PyPI (when published)
   pip install ai-guard
   
   # From local development
   pip install -e ../ai-guard
   ```

3. **Verify installation:**
   ```bash
   ai-guard --help
   ```

## 🧪 Running Tests

### Basic Quality Check
```bash
# Run all quality gates
ai-guard check

# Run with custom coverage threshold
ai-guard check --min-cov 90

# Skip tests for quick analysis
ai-guard check --skip-tests
```

### Generate Reports
```bash
# SARIF format (GitHub Code Scanning)
ai-guard check --report-format sarif --report-path results.sarif

# JSON format (CI automation)
ai-guard check --report-format json --report-path quality.json

# HTML format (human readable)
ai-guard check --report-format html --report-path report.html
```

## 🔧 CI/CD Integration

### GitHub Actions Example
```yaml
name: AI-Guard Quality Gates

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install AI-Guard
        run: pip install ai-guard
      
      - name: Run Quality Gates
        run: ai-guard check --min-cov 80 --report-format json
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: ai-guard.sarif
```

### GitLab CI Example
```yaml
stages:
  - quality

ai-guard:
  stage: quality
  image: python:3.11
  before_script:
    - pip install ai-guard
  script:
    - ai-guard check --min-cov 80 --report-format json
  artifacts:
    reports:
      codequality: quality.json
```

### Jenkins Pipeline Example
```groovy
pipeline {
    agent any
    
    stages {
        stage('Quality Gates') {
            steps {
                sh 'pip install ai-guard'
                sh 'ai-guard check --min-cov 80 --report-format json'
            }
            post {
                always {
                    publishJSON([
                        target: [
                            reportDir: '.',
                            reportFiles: 'quality.json',
                            reportName: 'AI-Guard Quality Report'
                        ]
                    ])
                }
            }
        }
    }
}
```

## 📊 Monitoring and Reporting

### Quality Metrics
- **Code Coverage**: Minimum threshold enforcement
- **Security Issues**: Automated vulnerability detection
- **Code Quality**: Linting and type checking
- **Test Generation**: Speculative test creation

### Report Formats
- **SARIF**: GitHub Code Scanning integration
- **JSON**: CI/CD automation and parsing
- **HTML**: Human-readable reports and dashboards

## 🛠️ Configuration

### AI-Guard Configuration File
Create `ai-guard.toml` in your project root:

```toml
[tool.ai-guard]
min_coverage = 80
quality_threshold = 85
skip_tests = false
report_format = "sarif"
report_path = "ai-guard.sarif"

[tool.ai-guard.gates]
linting = true
type_checking = true
security_scanning = true
coverage_enforcement = true
test_generation = true

[tool.ai-guard.security]
bandit_config = ".bandit"
exclude_patterns = ["tests/*", "docs/*"]

[tool.ai-guard.coverage]
exclude_patterns = ["tests/*", "docs/*", "migrations/*"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes your project
2. **Coverage Issues**: Check that tests are discoverable
3. **Security Scan Failures**: Review .bandit configuration
4. **Report Generation**: Verify write permissions for output files

### Debug Mode
```bash
# Enable verbose output
ai-guard check --verbose

# Debug mode with extra logging
DEBUG=1 ai-guard check
```

## 📈 Performance Monitoring

### Metrics to Track
- **Build Time**: How long quality gates take
- **Success Rate**: Percentage of builds passing gates
- **Issue Detection**: Number of problems found
- **Test Generation**: Coverage improvement over time

### Integration with Monitoring Tools
- **Prometheus**: Export metrics for alerting
- **Grafana**: Create dashboards for quality trends
- **Slack/Teams**: Notifications for gate failures

## 🎉 Success Criteria

A successful AI-Guard integration should demonstrate:
- ✅ Automated quality enforcement
- ✅ Improved code coverage over time
- ✅ Reduced security vulnerabilities
- ✅ Faster feedback loops
- ✅ Better code quality metrics

## 📚 Additional Resources

- [AI-Guard Documentation](https://github.com/Manavj99/ai-guard)
- [GitHub Code Scanning](https://docs.github.com/en/code-security/code-scanning)
- [SARIF Specification](https://sarifweb.azurewebsites.net/)
- [Bandit Security Scanner](https://bandit.readthedocs.io/)
