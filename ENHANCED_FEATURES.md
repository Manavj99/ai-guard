# 🚀 AI-Guard Enhanced Features

This document describes the new enhanced features added to AI-Guard, including enhanced test generation with LLM integration, JavaScript/TypeScript support, and advanced PR annotations.

## 🔧 Enhanced Test Generation

### Overview

The enhanced test generation system goes beyond basic test scaffolding to provide intelligent, context-aware test generation using LLM integration and advanced code analysis.

### Features

- **🤖 LLM Integration**: Connect to OpenAI, Anthropic, or local LLMs for intelligent test generation
- **🎯 Context-Aware Analysis**: Analyze actual code changes and generate meaningful tests
- **📋 Test Templates**: Customizable test templates for different code patterns
- **📊 Coverage Gap Analysis**: Identify uncovered code paths and suggest specific tests
- **🔍 AST Analysis**: Parse Python code to understand structure and generate appropriate tests

### Usage

#### Basic Enhanced Test Generation

```bash
# Enable enhanced test generation with OpenAI
python -m src.ai_guard.analyzer \
  --enhanced-testgen \
  --llm-provider openai \
  --llm-api-key your-api-key \
  --event "$GITHUB_EVENT_PATH"

# Use Anthropic Claude
python -m src.ai_guard.analyzer \
  --enhanced-testgen \
  --llm-provider anthropic \
  --llm-api-key your-api-key \
  --event "$GITHUB_EVENT_PATH"
```

#### Configuration

Create an `ai-guard-testgen.toml` configuration file:

```toml
[llm]
provider = "openai"
api_key = ""  # Can also use environment variables
model = "gpt-4"
temperature = 0.1

[test_generation]
framework = "pytest"
generate_mocks = true
generate_parametrized_tests = true
generate_edge_cases = true
max_tests_per_file = 10

[coverage_analysis]
analyze_coverage_gaps = true
min_coverage_threshold = 80.0

[output]
output_directory = "tests/unit"
test_file_suffix = "_test.py"
```

#### Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# Generic AI-Guard
export AI_GUARD_API_KEY="your-key"
export AI_GUARD_LLM_PROVIDER="openai"
export AI_GUARD_LLM_MODEL="gpt-4"
```

### How It Works

1. **Code Change Analysis**: Analyzes Git diffs to identify changed functions and classes
2. **AST Parsing**: Parses Python code to understand structure, arguments, and context
3. **LLM Integration**: Uses LLM to generate intelligent, context-aware tests
4. **Template Fallback**: Falls back to built-in templates if LLM is unavailable
5. **Coverage Analysis**: Identifies uncovered code paths and suggests specific tests

### Example Generated Tests

```python
# Auto-generated tests using AI-Guard Enhanced Test Generator
# Generated for the following changed files:
# - src/ai_guard/analyzer.py

import pytest
from unittest.mock import Mock, patch

# Test imports
try:
    from src.ai_guard.analyzer import *
except ImportError:
    pass  # Tests will fail if imports don't work

# Tests for src/ai_guard/analyzer.py
def test_analyzer_main_function():
    """Test analyzer main function."""
    # Arrange
    # Setup test data for main function
    
    # Act
    result = main_function(test_params)
    
    # Assert
    assert result is not None
    assert isinstance(result, (str, int, float, bool))

def test_analyzer_main_function_edge_cases():
    """Test analyzer main function with edge cases."""
    # Test with None
    with pytest.raises(ValueError):
        main_function(None)
    
    # Test with empty input
    result = main_function("")
    assert result == expected_empty_result
    
    # Test with extreme values
    result = main_function(extreme_value)
    assert result == expected_extreme_result
```

## 🌐 JavaScript/TypeScript Support

### Overview

AI-Guard now supports JavaScript and TypeScript projects with integration for ESLint, Prettier, Jest, and TypeScript compiler.

### Features

- **🔍 ESLint Integration**: Run ESLint for code quality and style checking
- **✨ Prettier Integration**: Check code formatting with Prettier
- **🧪 Jest Integration**: Run tests and generate test templates
- **📝 TypeScript Support**: Type checking and compilation
- **📦 Package.json Detection**: Automatic tool detection from package.json

### Usage

#### Basic JavaScript/TypeScript Support

```bash
# Check dependencies
python -m src.ai_guard.language_support.js_ts_support --check-deps

# Run quality checks
python -m src.ai_guard.language_support.js_ts_support \
  --quality \
  --files src/**/*.js src/**/*.ts

# Generate test files
python -m src.ai_guard.language_support.js_ts_support \
  --generate-tests \
  --files src/**/*.js \
  --output-dir tests
```

#### Configuration

The system automatically detects configuration from your `package.json`:

```json
{
  "devDependencies": {
    "eslint": "^8.0.0",
    "prettier": "^2.8.0",
    "jest": "^29.0.0",
    "typescript": "^5.0.0"
  },
  "scripts": {
    "test": "jest",
    "lint": "eslint src/**/*.js",
    "format": "prettier --check src/**/*.js"
  }
}
```

#### Quality Checks

The system runs the following quality checks:

1. **ESLint**: Code quality and style rules
2. **Prettier**: Code formatting consistency
3. **TypeScript**: Type checking and compilation
4. **Jest**: Test execution and coverage

#### Test Generation

Generates Jest-compatible test templates:

```javascript
// Auto-generated test file for src/components/Button.js
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Import the module to test
const { Button } = require('./Button');

describe('Button', () => {
  test('should render without crashing', () => {
    // TODO: Implement test
    expect(true).toBe(true);
  });

  test('should handle user interactions', () => {
    // TODO: Implement test
    expect(true).toBe(true);
  });

  test('should handle edge cases', () => {
    // TODO: Implement test
    expect(true).toBe(true);
  });
});
```

## 📝 PR Annotations

### Overview

The PR annotation system provides comprehensive GitHub integration with inline comments, suggestion blocks, and detailed review summaries.

### Features

- **📍 Inline Comments**: Add specific feedback on problematic lines
- **💡 Suggestion Blocks**: Provide code suggestions for fixes
- **📋 Review Templates**: Generate comprehensive PR review summaries
- **🎯 Quality Scoring**: Calculate overall quality scores
- **🔍 Issue Categorization**: Group issues by severity and type

### Usage

#### Enable PR Annotations

```bash
# Generate PR annotations
python -m src.ai_guard.analyzer \
  --pr-annotations \
  --annotations-output pr-review.json \
  --event "$GITHUB_EVENT_PATH"
```

#### Annotation Types

1. **Linting Issues**: ESLint, flake8, mypy violations
2. **Security Issues**: Bandit security findings
3. **Coverage Issues**: Uncovered code lines
4. **Code Quality**: Style and formatting issues

#### Example Annotations

```json
{
  "annotations": [
    {
      "file_path": "src/analyzer.py",
      "line_number": 42,
      "message": "E501: line too long (127 > 79 characters)\n💡 **Suggestion:** Consider breaking this long line into multiple lines",
      "annotation_level": "warning",
      "title": "E501: line too long (127 > 79 characters)",
      "start_line": 42,
      "end_line": 42
    }
  ],
  "summary": {
    "overall_status": "commented",
    "quality_score": 0.85,
    "suggestions": [
      "Consider using a line length formatter like `black` or `autopep8`"
    ]
  }
}
```

#### Review Summary

The system generates comprehensive review summaries:

```markdown
## 🤖 AI-Guard Quality Review

**Status:** Commented
**Quality Score:** 85%

### 📊 Summary
⚠️ 3 warnings | ℹ️ 2 suggestions

### 💡 Suggestions
- Consider using a line length formatter like `black` or `autopep8`
- Run `isort` to organize imports and remove unused ones

### 🔍 Issues Found
Total annotations: 5

**src/analyzer.py:**
- ⚠️ Line 42: E501: line too long (127 > 79 characters)
- ⚠️ Line 67: F401: 'unused_import' imported but unused
- ... and 3 more issues

---
*This review was automatically generated by AI-Guard*
```

## 🔧 Integration Examples

### GitHub Actions with Enhanced Features

```yaml
name: AI-Guard Enhanced CI/CD

on: [pull_request, push]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -e .
      
      - name: Run AI-Guard with Enhanced Features
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m src.ai_guard.analyzer \
            --enhanced-testgen \
            --llm-provider openai \
            --pr-annotations \
            --annotations-output pr-review.json \
            --event "$GITHUB_EVENT_PATH" \
            --report-format sarif \
            --report-path ai-guard.sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: ai-guard.sarif
      
      - name: Upload PR Review
        uses: actions/upload-artifact@v4
        with:
          name: pr-review
          path: pr-review.json
```

### Multi-Language Project

```yaml
name: Multi-Language Quality Gates

on: [pull_request]

jobs:
  python-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Quality Gates
        run: |
          python -m src.ai_guard.analyzer \
            --enhanced-testgen \
            --pr-annotations

  javascript-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: JavaScript/TypeScript Quality Gates
        run: |
          python -m src.ai_guard.language_support.js_ts_support \
            --quality \
            --files src/**/*.js src/**/*.ts
```

## 🚀 Getting Started

### 1. Install Enhanced Dependencies

```bash
# For enhanced test generation
pip install openai anthropic

# For JavaScript/TypeScript support
npm install --save-dev eslint prettier jest typescript
```

### 2. Configure LLM Integration

```bash
# Set API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Or use configuration file
python -m src.ai_guard.generators.config_loader
```

### 3. Run Enhanced Analysis

```bash
# Basic enhanced analysis
python -m src.ai_guard.analyzer --enhanced-testgen

# Full enhanced analysis with PR annotations
python -m src.ai_guard.analyzer \
  --enhanced-testgen \
  --pr-annotations \
  --event "$GITHUB_EVENT_PATH"
```

### 4. JavaScript/TypeScript Support

```bash
# Check your setup
python -m src.ai_guard.language_support.js_ts_support --check-deps

# Run quality checks
python -m src.ai_guard.language_support.js_ts_support --quality --files src/**/*.js
```

## 🔍 Troubleshooting

### Common Issues

1. **LLM API Key Not Found**
   - Set environment variables: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
   - Check configuration file: `ai-guard-testgen.toml`

2. **Enhanced Test Generation Fails**
   - Ensure changed files are Python files
   - Check LLM API key and provider settings
   - Verify network connectivity for API calls

3. **JavaScript/TypeScript Tools Not Found**
   - Install required npm packages
   - Check `package.json` dependencies
   - Ensure tools are available in PATH

4. **PR Annotations Not Generated**
   - Enable with `--pr-annotations` flag
   - Check GitHub event file path
   - Verify output file permissions

### Debug Mode

```bash
# Enable debug logging
export PYTHONPATH=src
python -m src.ai_guard.analyzer \
  --enhanced-testgen \
  --pr-annotations \
  --event "$GITHUB_EVENT_PATH" \
  --report-format json
```

## 📚 Advanced Configuration

### Custom Test Templates

Create custom test templates in `ai-guard-testgen.toml`:

```toml
[templates]
custom_template_dir = "custom_templates"
function_template = "custom_function_test"
class_template = "custom_class_test"
```

### Custom Quality Rules

Extend the PR annotation system with custom rules:

```python
from src.ai_guard.pr_annotations import PRAnnotator, CodeIssue

annotator = PRAnnotator()

# Add custom issue
custom_issue = CodeIssue(
    file_path="src/custom.py",
    line_number=10,
    column=5,
    severity="warning",
    message="Custom quality rule violation",
    rule_id="custom:rule1"
)
annotator.add_issue(custom_issue)
```

### Integration with External Tools

```python
# Integrate with custom linting tools
from src.ai_guard.language_support.js_ts_support import JavaScriptTypeScriptSupport

js_support = JavaScriptTypeScriptSupport(config)

# Run custom quality checks
results = js_support.run_custom_quality_check(file_paths)
```

## 🎯 Future Enhancements

- **🔗 More LLM Providers**: Support for local models, Azure OpenAI, etc.
- **🌍 Additional Languages**: Go, Rust, Java, C# support
- **🤖 AI-Powered Fixes**: Automatic code fixes using LLMs
- **📊 Advanced Analytics**: Trend analysis and quality metrics
- **🔌 Plugin System**: Extensible architecture for custom tools

---

**Need Help?** Check the main [README.md](README.md) or create an issue for support.
