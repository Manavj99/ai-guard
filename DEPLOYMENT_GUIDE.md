# AI-Guard CI/CD Deployment Guide

This guide provides comprehensive instructions for deploying AI-Guard in various CI/CD environments and monitoring workflow progress.

## 🎯 Overview

AI-Guard is designed to integrate seamlessly with CI/CD pipelines to enforce code quality gates and provide comprehensive reporting. This guide covers:

1. **Workflow Progress Monitoring** - Track CI/CD pipeline status
2. **Installation Testing** - Verify AI-Guard works after publication
3. **CI/CD Pipeline Setup** - Integration with various platforms
4. **Test Project Verification** - End-to-end testing

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Access to AI-Guard package (when published)
- CI/CD platform access (GitHub Actions, GitLab CI, Jenkins, etc.)

### 1. Install AI-Guard
```bash
# From PyPI (when published)
pip install ai-guard

# Verify installation
ai-guard --help
```

### 2. Basic Integration
```bash
# Run quality gates
ai-guard check --min-cov 80 --report-format json

# Generate SARIF for GitHub Code Scanning
ai-guard check --report-format sarif --report-path results.sarif
```

## 📊 Workflow Progress Monitoring

### GitHub Actions Monitoring

#### Real-time Status
- **Actions Tab**: Monitor workflow runs in real-time
- **Status Badges**: Display in README for quick status
- **Notifications**: Configure email/Slack notifications

#### Progress Tracking
```yaml
# Enhanced workflow with progress indicators
- name: 📊 Progress Update
  run: |
    echo "🔄 Step 3/6: Running quality gates..."
    echo "⏱️ Elapsed time: ${{ steps.timer.outputs.elapsed }}"
    echo "📈 Quality score: ${{ steps.quality-check.outputs.score }}%"
```

#### Status Dashboard
Create a status dashboard using GitHub Pages or external tools:

```html
<!-- status.html -->
<div class="status-dashboard">
  <div class="status-item">
    <span class="label">Quality Gates:</span>
    <span class="value" id="quality-score">--</span>
  </div>
  <div class="status-item">
    <span class="label">Coverage:</span>
    <span class="value" id="coverage">--</span>
  </div>
  <div class="status-item">
    <span class="label">Security:</span>
    <span class="value" id="security">--</span>
  </div>
</div>
```

### Metrics Collection

#### Key Metrics to Track
- **Build Time**: Total pipeline execution time
- **Success Rate**: Percentage of builds passing gates
- **Quality Score**: AI-Guard quality assessment
- **Coverage Trend**: Code coverage over time
- **Security Issues**: Number of vulnerabilities found

#### Prometheus Integration
```yaml
# Export metrics for monitoring
- name: Export Metrics
  run: |
    echo "ai_guard_quality_score ${{ steps.quality-check.outputs.score }}" >> metrics.txt
    echo "ai_guard_coverage ${{ steps.coverage-check.outputs.percentage }}" >> metrics.txt
    echo "ai_guard_security_issues ${{ steps.security-scan.outputs.issues }}" >> metrics.txt
```

## 🧪 Installation Testing

### Post-Publication Verification

#### 1. Package Installation Test
```bash
# Test in clean environment
python -m venv test-env
source test-env/bin/activate  # Linux/Mac
# or
test-env\Scripts\activate     # Windows

# Install from PyPI
pip install ai-guard

# Verify installation
ai-guard --help
python -c "import ai_guard; print('✅ Import successful')"
```

#### 2. Functionality Test
```bash
# Test basic functionality
ai-guard check --help
ai-guard check --version

# Test with sample project
git clone <your-test-repo>
cd <test-repo>
ai-guard check --min-cov 80 --skip-tests
```

#### 3. Integration Test
```yaml
# GitHub Actions test workflow
name: Test AI-Guard Installation

on: [workflow_dispatch]

jobs:
  test-installation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install AI-Guard
        run: pip install ai-guard
      
      - name: Test functionality
        run: |
          ai-guard --help
          ai-guard check --help
          python -c "import ai_guard; print('Import successful')"
```

## 🔧 CI/CD Pipeline Setup

### GitHub Actions

#### Basic Integration
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

#### Advanced Integration with Progress Monitoring
```yaml
name: AI-Guard Enhanced

on: [push, pull_request]

env:
  PYTHON_VERSION: '3.11'
  MIN_COVERAGE: 80

jobs:
  quality-gates:
    name: 🎯 Quality Gates
    runs-on: ubuntu-latest
    
    outputs:
      quality-score: ${{ steps.quality-check.outputs.score }}
      coverage: ${{ steps.coverage-check.outputs.percentage }}
    
    steps:
      - name: 📥 Checkout
        uses: actions/checkout@v4
      
      - name: 🐍 Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: 📦 Install AI-Guard
        run: pip install ai-guard
      
      - name: 🎯 Run Quality Gates
        id: quality-check
        run: |
          echo "🎯 Running AI-Guard quality gates..."
          ai-guard check \
            --min-cov ${{ env.MIN_COVERAGE }} \
            --skip-tests \
            --report-format json \
            --report-path quality.json
          
          # Extract quality score
          SCORE=$(python -c "
          import json
          with open('quality.json', 'r') as f:
              data = json.load(f)
              print(data.get('summary', {}).get('score', 0))
          ")
          echo "score=$SCORE" >> $GITHUB_OUTPUT
      
      - name: 📊 Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: ai-guard.sarif
      
      - name: 📋 Status Report
        run: |
          echo "📊 Quality Gates Status:"
          echo "Quality Score: ${{ steps.quality-check.outputs.score }}%"
          echo "Coverage: ${{ steps.coverage-check.outputs.percentage }}%"
```

### GitLab CI

#### Basic Integration
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
    paths:
      - ai-guard.sarif
      - quality.json
```

#### Advanced Integration
```yaml
variables:
  PYTHON_VERSION: "3.11"
  MIN_COVERAGE: "80"

stages:
  - quality
  - report

quality-gates:
  stage: quality
  image: python:3.11
  before_script:
    - pip install ai-guard
  script:
    - echo "🎯 Running AI-Guard quality gates..."
    - ai-guard check --min-cov $MIN_COVERAGE --report-format json
    - echo "✅ Quality gates completed"
  artifacts:
    reports:
      codequality: quality.json
    paths:
      - quality.json
      - ai-guard.sarif
    expire_in: 1 week

quality-report:
  stage: report
  image: python:3.11
  dependencies:
    - quality-gates
  script:
    - echo "📊 Generating quality report..."
    - python -c "
      import json
      with open('quality.json', 'r') as f:
          data = json.load(f)
          print(f'Quality Score: {data.get(\"summary\", {}).get(\"score\", \"N/A\")}%')
          print(f'Gates Passed: {data.get(\"summary\", {}).get(\"gates_passed\", \"N/A\")}')
      "
  only:
    - main
    - merge_requests
```

### Jenkins Pipeline

#### Basic Pipeline
```groovy
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        MIN_COVERAGE = '80'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'python --version'
                sh 'pip install ai-guard'
            }
        }
        
        stage('Quality Gates') {
            steps {
                sh 'ai-guard check --min-cov ${MIN_COVERAGE} --report-format json'
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
    
    post {
        always {
            cleanWs()
        }
    }
}
```

#### Advanced Pipeline with Progress Monitoring
```groovy
pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        MIN_COVERAGE = '80'
        START_TIME = "${new Date().getTime()}"
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    echo "🚀 Starting AI-Guard pipeline..."
                    echo "⏰ Start time: ${new Date()}"
                }
                sh 'python --version'
                sh 'pip install ai-guard'
            }
        }
        
        stage('Quality Gates') {
            steps {
                script {
                    echo "🎯 Running quality gates..."
                    echo "📊 Coverage threshold: ${MIN_COVERAGE}%"
                }
                sh 'ai-guard check --min-cov ${MIN_COVERAGE} --report-format json'
            }
            post {
                always {
                    script {
                        def elapsed = (new Date().getTime() - env.START_TIME.toLong()) / 1000
                        echo "⏱️ Elapsed time: ${elapsed}s"
                    }
                }
            }
        }
        
        stage('Generate Report') {
            steps {
                script {
                    echo "📋 Generating comprehensive report..."
                    sh '''
                        python -c "
                        import json
                        with open('quality.json', 'r') as f:
                            data = json.load(f)
                            print('📊 Quality Report:')
                            print(f'  Score: {data.get(\"summary\", {}).get(\"score\", \"N/A\")}%')
                            print(f'  Gates: {data.get(\"summary\", {}).get(\"gates_passed\", \"N/A\")}/{data.get(\"summary\", {}).get(\"total_gates\", \"N/A\")}')
                        "
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "🎉 Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed!"
        }
        always {
            cleanWs()
        }
    }
}
```

## 🧪 Test Project Verification

### Project Structure
```
test-project/
├── src/
│   └── sample_app/
│       ├── __init__.py
│       └── calculator.py
├── tests/
│   └── test_calculator.py
├── .github/
│   └── workflows/
│       └── test-ai-guard.yml
├── pyproject.toml
├── requirements.txt
├── Makefile
└── README.md
```

### Verification Commands
```bash
# Navigate to test project
cd test-project

# Verify setup
make verify

# Install dependencies
make install

# Run tests
make test

# Test AI-Guard integration
make ai-guard-test
make ai-guard-check
make ai-guard-reports

# Run demo
make demo

# Simulate CI/CD pipeline
make ci-simulate
```

### Expected Results
- ✅ All tests pass with >80% coverage
- ✅ Linting passes without errors
- ✅ Type checking passes
- ✅ Security scan completes
- ✅ AI-Guard generates all report formats
- ✅ SARIF uploads to GitHub Code Scanning

## 📊 Monitoring and Alerting

### GitHub Notifications
```yaml
# Configure notifications in repository settings
notifications:
  email: true
  web: true
  slack: true  # Requires Slack integration
```

### External Monitoring
```yaml
# Prometheus metrics export
- name: Export Metrics
  run: |
    cat << EOF > metrics.txt
    # HELP ai_guard_quality_score Quality score from AI-Guard
    # TYPE ai_guard_quality_score gauge
    ai_guard_quality_score ${{ steps.quality-check.outputs.score }}
    
    # HELP ai_guard_build_duration Build duration in seconds
    # TYPE ai_guard_build_duration gauge
    ai_guard_build_duration ${{ steps.timer.outputs.elapsed }}
    EOF
```

### Slack/Teams Integration
```yaml
# Slack notification on failure
- name: Notify on Failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    text: "❌ AI-Guard quality gates failed for ${{ github.repository }}#${{ github.run_number }}"
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Check PYTHONPATH
echo $PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Verify installation
pip list | grep ai-guard
```

#### 2. Coverage Issues
```bash
# Check test discovery
python -m pytest --collect-only

# Verify source path
python -c "import sys; print(sys.path)"
```

#### 3. Report Generation Failures
```bash
# Check permissions
ls -la ai-guard.sarif

# Verify file paths
ai-guard check --report-format json --report-path ./test.json
```

#### 4. CI/CD Integration Issues
```yaml
# Debug mode
- name: Debug Environment
  run: |
    echo "Python version: $(python --version)"
    echo "Pip list:"
    pip list
    echo "Environment:"
    env | sort
    echo "Working directory: $(pwd)"
    echo "Files:"
    ls -la
```

## 📈 Performance Optimization

### Parallel Execution
```yaml
# Run quality checks in parallel
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [...]
  
  type-check:
    runs-on: ubuntu-latest
    steps: [...]
  
  security:
    runs-on: ubuntu-latest
    steps: [...]
  
  quality-gates:
    needs: [lint, type-check, security]
    runs-on: ubuntu-latest
    steps: [...]
```

### Caching
```yaml
# Cache dependencies
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Resource Optimization
```yaml
# Use larger runners for complex analysis
jobs:
  quality-gates:
    runs-on: ubuntu-latest-4-cores
    # or
    runs-on: ubuntu-latest-8-cores
```

## 🎉 Success Criteria

A successful AI-Guard deployment should demonstrate:

1. **✅ Automated Quality Enforcement**
   - Quality gates run on every PR
   - Coverage thresholds enforced
   - Security issues detected

2. **✅ Comprehensive Reporting**
   - SARIF integration with GitHub Code Scanning
   - JSON reports for CI automation
   - HTML reports for human review

3. **✅ Performance Metrics**
   - Build time < 5 minutes
   - Quality score > 85%
   - Coverage > 80%

4. **✅ Integration Success**
   - Works with existing CI/CD pipelines
   - Provides actionable feedback
   - Improves code quality over time

## 📚 Additional Resources

- [AI-Guard Documentation](https://github.com/Manavj99/ai-guard)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [SARIF Specification](https://sarifweb.azurewebsites.net/)

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review GitHub Issues in the AI-Guard repository
3. Create a new issue with detailed information
4. Include logs, error messages, and environment details
