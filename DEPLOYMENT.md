# AI-Guard Production Deployment Guide

This guide covers deploying AI-Guard in production CI/CD pipelines across different platforms and use cases.

## 🚀 Quick Start

### 1. GitHub Actions (Recommended)

AI-Guard is pre-configured with comprehensive GitHub Actions workflows:

- **Main CI**: Runs on every PR and push to main
- **Security**: Weekly security scans and dependency updates
- **Release**: Automated releases and Docker image builds
- **Matrix Testing**: Cross-platform and Python version testing

### 2. Docker Deployment

```bash
# Pull the latest image
docker pull ghcr.io/manavj99/ai-guard:latest

# Run quality checks
docker run --rm -v "$PWD":/workspace ghcr.io/manavj99/ai-guard:latest \
  --min-cov 85 \
  --report-format sarif \
  --report-path /workspace/ai-guard.sarif
```

## 🔧 CI/CD Integration Patterns

### GitHub Actions

#### Basic Integration
```yaml
name: Quality Gate
on: [pull_request, push]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ai-guard
      - run: ai-guard check --min-cov 80
```

#### Advanced Integration with SARIF
```yaml
- name: Run AI-Guard
  run: |
    ai-guard check \
      --min-cov 85 \
      --skip-tests \
      --event "$GITHUB_EVENT_PATH" \
      --report-format sarif \
      --report-path ai-guard.sarif

- name: Upload SARIF to code scanning
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: ai-guard.sarif
```

### GitLab CI

```yaml
quality-gate:
  image: ghcr.io/manavj99/ai-guard:latest
  stage: test
  script:
    - ai-guard check --min-cov 80 --report-format json
  artifacts:
    reports:
      junit: ai-guard.xml
    paths:
      - ai-guard.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Quality Gate') {
            steps {
                script {
                    def qualityResult = sh(
                        script: 'ai-guard check --min-cov 80 --report-format json',
                        returnStdout: true
                    ).trim()
                    
                    def result = readJSON text: qualityResult
                    if (!result.summary.passed) {
                        error "Quality gates failed: ${result.summary.gates.findAll { !it.passed }.collect { it.name }}"
                    }
                }
            }
        }
    }
}
```

### Azure DevOps

```yaml
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.11'

- script: |
    pip install ai-guard
  displayName: 'Install AI-Guard'

- script: |
    ai-guard check --min-cov 80 --report-format json
  displayName: 'Run Quality Gates'
```

## 🐳 Docker Integration

### Multi-stage Dockerfile
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
RUN pip install ai-guard

# Quality gate stage
FROM ai-guard:latest as quality-check
COPY . /workspace
WORKDIR /workspace
RUN ai-guard check --min-cov 80
```

### Docker Compose
```yaml
version: '3.8'
services:
  ai-guard:
    image: ghcr.io/manavj99/ai-guard:latest
    volumes:
      - .:/workspace
    command: --min-cov 80 --report-format html
    environment:
      - PYTHONPATH=/workspace
```

## 🔒 Security Integration

### Bandit Security Scanning
```yaml
- name: Security Scan
  run: |
    ai-guard check \
      --min-cov 80 \
      --skip-tests \
      --security-only \
      --report-format sarif \
      --report-path security.sarif
```

### Dependency Vulnerability Scanning
```yaml
- name: Check Dependencies
  run: |
    pip-audit -r requirements.txt --format json --output pip-audit.json
    ai-guard check --dependencies-only
```

## 📊 Reporting Integration

### SARIF for GitHub Code Scanning
```yaml
- name: Generate SARIF
  run: |
    ai-guard check \
      --min-cov 80 \
      --report-format sarif \
      --report-path ai-guard.sarif

- name: Upload to Code Scanning
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: ai-guard.sarif
```

### JSON for CI Decision Making
```yaml
- name: Quality Check
  run: |
    ai-guard check \
      --min-cov 80 \
      --report-format json \
      --report-path quality.json

- name: Parse Results
  run: |
    if python -c "import json; data=json.load(open('quality.json')); exit(0 if data['summary']['passed'] else 1)"; then
      echo "✅ All gates passed"
    else
      echo "❌ Some gates failed"
      exit 1
    fi
```

### HTML for CI Artifacts
```yaml
- name: Generate HTML Report
  run: |
    ai-guard check \
      --min-cov 80 \
      --report-format html \
      --report-path ai-guard.html

- name: Upload Artifact
  uses: actions/upload-artifact@v4
  with:
    name: quality-report
    path: ai-guard.html
    retention-days: 30
```

## ⚙️ Configuration Management

### Environment-based Configuration
```yaml
- name: Quality Gate
  env:
    AI_GUARD_MIN_COV: ${{ secrets.MIN_COVERAGE || 80 }}
    AI_GUARD_CONFIG: ${{ secrets.AI_GUARD_CONFIG }}
  run: |
    ai-guard check \
      --min-cov $AI_GUARD_MIN_COV \
      --config $AI_GUARD_CONFIG
```

### Configuration File
```toml
# ai-guard.toml
[gates]
min_coverage = 85
skip_tests = false

[security]
bandit_skips = ["B101", "B601"]
severity_threshold = "Medium"

[reporting]
formats = ["sarif", "json", "html"]
output_dir = "reports/"
```

## 🚨 Failure Handling

### Graceful Degradation
```yaml
- name: Quality Gate
  continue-on-error: true
  run: |
    ai-guard check --min-cov 80 || {
      echo "Quality gates failed, but continuing..."
      exit 0
    }
```

### Conditional Failure
```yaml
- name: Quality Gate
  run: |
    ai-guard check --min-cov 80 --report-format json --report-path result.json
    
    # Only fail on high-severity issues
    python -c "
    import json
    with open('result.json') as f:
        data = json.load(f)
        high_severity = [r for r in data.get('findings', []) if r.get('level') == 'error']
        if high_severity:
            print(f'Found {len(high_severity)} high-severity issues')
            exit(1)
    "
```

## 📈 Monitoring and Metrics

### Coverage Tracking
```yaml
- name: Coverage Report
  run: |
    ai-guard check --min-cov 80 --report-format json --report-path coverage.json
    
    # Extract coverage percentage
    COVERAGE=$(python -c "
    import json
    with open('coverage.json') as f:
        data = json.load(f)
        print(data['summary']['coverage']['percentage'])
    ")
    
    echo "coverage=$COVERAGE" >> $GITHUB_OUTPUT
```

### Quality Metrics Dashboard
```yaml
- name: Generate Metrics
  run: |
    ai-guard check --report-format json --report-path metrics.json
    
    # Create summary for dashboard
    python -c "
    import json
    with open('metrics.json') as f:
        data = json.load(f)
        summary = {
            'total_issues': len(data.get('findings', [])),
            'gates_passed': sum(1 for g in data['summary']['gates'] if g['passed']),
            'total_gates': len(data['summary']['gates']),
            'coverage': data['summary']['coverage']['percentage']
        }
        print(json.dumps(summary))
    " > summary.json
```

## 🔄 Advanced Workflows

### Multi-Repository Scanning
```yaml
- name: Scan Multiple Repos
  run: |
    for repo in repo1 repo2 repo3; do
      git clone https://github.com/org/$repo.git
      cd $repo
      ai-guard check --min-cov 80 --report-format json --report-path ../$repo-quality.json
      cd ..
    done
    
    # Aggregate results
    python aggregate_results.py *.json
```

### Incremental Quality Gates
```yaml
- name: Incremental Check
  run: |
    # Only check changed files
    CHANGED_FILES=$(git diff --name-only HEAD~1 | grep '\.py$' | tr '\n' ' ')
    
    if [ -n "$CHANGED_FILES" ]; then
      ai-guard check \
        --min-cov 80 \
        --files $CHANGED_FILES \
        --report-format json
    else
      echo "No Python files changed"
    fi
```

## 🆘 Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure proper GitHub token permissions
2. **Coverage Failures**: Check if tests are generating coverage data
3. **Security Scan Failures**: Verify Bandit configuration
4. **Docker Issues**: Check image tags and volume mounts

### Debug Mode
```yaml
- name: Debug Quality Gate
  run: |
    ai-guard check \
      --min-cov 80 \
      --verbose \
      --debug \
      --report-format json
```

### Log Analysis
```yaml
- name: Collect Logs
  if: failure()
  run: |
    echo "=== AI-Guard Logs ==="
    cat ai-guard.log || echo "No log file found"
    
    echo "=== Environment Info ==="
    python --version
    pip list | grep ai-guard
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [SARIF Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- [CI/CD Best Practices](https://martinfowler.com/articles/continuousIntegration.html)

---

**Need Help?** Open an issue on GitHub or check the [README.md](README.md) for more information.
