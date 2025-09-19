# Contributing to AI Guard 🛡️

Thank you for your interest in contributing to AI Guard! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Node.js (for JavaScript/TypeScript support)
- Basic understanding of code quality tools (flake8, mypy, bandit, etc.)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-guard.git
   cd ai-guard
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   pre-commit install
   ```

4. **Verify installation**
   ```bash
   ai-guard --version
   pytest tests/
   ```

## 📋 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Write clean, well-documented code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests and Quality Checks

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src --cov-report=html

# Format code
black src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/

# Linting
flake8 src/ tests/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `perf:` for performance improvements
- `chore:` for maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 🧪 Testing Guidelines

### Test Structure

- Place tests in the `tests/` directory
- Use descriptive test names
- Group related tests in classes
- Use fixtures for common setup

### Test Coverage

- Aim for 90%+ test coverage
- Test both happy path and edge cases
- Include integration tests for complex workflows
- Mock external dependencies appropriately

### Example Test Structure

```python
"""Tests for module_name."""

import pytest
from src.ai_guard.module_name import ClassName


class TestClassName:
    """Test ClassName functionality."""

    def test_method_success(self):
        """Test successful method execution."""
        # Arrange
        instance = ClassName()
        
        # Act
        result = instance.method()
        
        # Assert
        assert result is not None

    def test_method_with_invalid_input(self):
        """Test method with invalid input."""
        # Arrange
        instance = ClassName()
        
        # Act & Assert
        with pytest.raises(ValueError):
            instance.method(invalid_input)
```

## 📝 Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints for all functions and methods
- Write comprehensive docstrings
- Keep functions small and focused
- Use meaningful variable names

### Documentation

- Write clear docstrings for all public functions/classes
- Include examples in docstrings where helpful
- Update README.md for user-facing changes
- Document configuration options

### Example Function Documentation

```python
def analyze_code(
    file_path: str, 
    config: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    Analyze code for quality issues.

    Args:
        file_path: Path to the file to analyze
        config: Optional configuration dictionary

    Returns:
        AnalysisResult containing analysis findings

    Raises:
        FileNotFoundError: If file_path doesn't exist
        ValueError: If file_path is invalid

    Example:
        >>> result = analyze_code("src/main.py")
        >>> print(f"Found {len(result.issues)} issues")
    """
```

## 🔧 Configuration and Environment

### Environment Variables

- `AI_GUARD_RULE_ID_STYLE`: Rule ID formatting style
- `GITHUB_TOKEN`: GitHub API token for PR annotations
- `GITHUB_REPOSITORY`: Repository name for GitHub integration
- `AI_GUARD_PERFORMANCE_MODE`: Performance monitoring mode

### Configuration Files

- `ai-guard.toml`: Main configuration file
- `pyproject.toml`: Project metadata and tool configuration
- `.pre-commit-config.yaml`: Pre-commit hooks configuration

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information**
   - Python version
   - Operating system
   - AI Guard version

2. **Steps to reproduce**
   - Clear, numbered steps
   - Sample code if applicable

3. **Expected vs actual behavior**
   - What you expected to happen
   - What actually happened

4. **Additional context**
   - Error messages/logs
   - Configuration files
   - Screenshots if relevant

## 💡 Feature Requests

When suggesting features:

1. **Describe the problem**
   - What problem does this solve?
   - Who would benefit from this feature?

2. **Propose a solution**
   - How should this feature work?
   - Any specific requirements or constraints?

3. **Consider alternatives**
   - Are there other ways to solve this problem?
   - What are the trade-offs?

## 🏗️ Architecture Guidelines

### Module Organization

- Keep modules focused and cohesive
- Use clear separation of concerns
- Minimize coupling between modules
- Follow the existing package structure

### Error Handling

- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Handle edge cases gracefully

### Performance Considerations

- Profile code for performance bottlenecks
- Use appropriate data structures
- Consider memory usage
- Optimize critical paths

## 📚 Resources

- [Python Documentation](https://docs.python.org/3/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [MyPy Type Checker](https://mypy.readthedocs.io/)
- [Bandit Security Linter](https://bandit.readthedocs.io/)

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different perspectives and experiences

### Communication

- Use clear, professional language
- Be specific in bug reports and feature requests
- Ask questions when you need clarification
- Help others when you can

## 📞 Getting Help

- 📖 [Documentation](https://ai-guard.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/ai-guard/ai-guard/issues)
- 💬 [Discussions](https://github.com/ai-guard/ai-guard/discussions)
- 📧 [Email Support](mailto:support@ai-guard.dev)

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to AI Guard! 🛡️
