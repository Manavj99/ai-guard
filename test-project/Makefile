.PHONY: help install test lint type-check security coverage clean ai-guard-test ai-guard-reports

help:  ## Show this help message
	@echo "AI-Guard Test Project Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt

test:  ## Run tests with coverage
	export PYTHONPATH="$(PWD)/src"
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

lint:  ## Run flake8 linting
	flake8 src tests

type-check:  ## Run mypy type checking
	mypy src

security:  ## Run security scans
	bandit -r src -c .bandit

coverage:  ## Run tests and generate coverage report
	export PYTHONPATH="$(PWD)/src"
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=xml

clean:  ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml
	rm -f *.sarif
	rm -f *.json
	rm -f *.html
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

all: lint type-check security test  ## Run all quality checks

ai-guard-test:  ## Test AI-Guard installation and basic functionality
	@echo "🧪 Testing AI-Guard installation..."
	@ai-guard --help || (echo "❌ AI-Guard not installed. Install it first." && exit 1)
	@echo "✅ AI-Guard is installed and working"

ai-guard-check:  ## Run AI-Guard quality gates
	@echo "🎯 Running AI-Guard quality gates..."
	export PYTHONPATH="$(PWD)/src"
	ai-guard check --min-cov 80 --skip-tests --report-format json --report-path quality-check.json
	@echo "✅ Quality gates completed"

ai-guard-reports:  ## Test all AI-Guard report formats
	@echo "📊 Testing AI-Guard report generation..."
	export PYTHONPATH="$(PWD)/src"
	
	@echo "📄 Testing SARIF format..."
	ai-guard check --skip-tests --report-format sarif --report-path test-sarif.sarif
	
	@echo "📄 Testing JSON format..."
	ai-guard check --skip-tests --report-format json --report-path test-json.json
	
	@echo "📄 Testing HTML format..."
	ai-guard check --skip-tests --report-format html --report-path test-html.html
	
	@echo "✅ All report formats tested successfully"

ai-guard-full:  ## Run full AI-Guard analysis with tests
	@echo "🚀 Running full AI-Guard analysis..."
	export PYTHONPATH="$(PWD)/src"
	ai-guard check --min-cov 80 --report-format json --report-path full-analysis.json
	@echo "✅ Full analysis completed"

demo:  ## Run a quick demo of the sample application
	@echo "🎮 Running sample application demo..."
	export PYTHONPATH="$(PWD)/src"
	python -c "
from sample_app.calculator import Calculator, quick_add, quick_multiply

print('🧮 AI-Guard Test Project Demo')
print('=' * 40)

# Test basic calculator
calc = Calculator(precision=3)
print(f'2 + 3 = {calc.add(2, 3)}')
print(f'5 * 4 = {calc.multiply(5, 4)}')
print(f'10 / 3 = {calc.divide(10, 3)}')
print(f'sqrt(16) = {calc.sqrt(16)}')

# Test quick functions
print(f'Quick add: 7 + 8 = {quick_add(7, 8)}')
print(f'Quick multiply: 6 * 9 = {quick_multiply(6, 9)}')

# Show history
print(f'\\nCalculation history:')
for op in calc.get_history():
    print(f'  {op}')

print('\\n✅ Demo completed successfully!')
"
	@echo "✅ Demo completed"

ci-simulate:  ## Simulate CI/CD pipeline locally
	@echo "🏭 Simulating CI/CD pipeline..."
	@echo "Step 1: Installing dependencies..."
	@make install
	@echo "Step 2: Running quality checks..."
	@make all
	@echo "Step 3: Testing AI-Guard..."
	@make ai-guard-test
	@echo "Step 4: Running AI-Guard quality gates..."
	@make ai-guard-check
	@echo "Step 5: Testing report generation..."
	@make ai-guard-reports
	@echo "Step 6: Running full analysis..."
	@make ai-guard-full
	@echo "🎉 CI/CD simulation completed successfully!"

verify:  ## Verify everything is working correctly
	@echo "🔍 Verifying AI-Guard test project setup..."
	@echo "Checking file structure..."
	@test -f src/sample_app/__init__.py || (echo "❌ Missing src/sample_app/__init__.py" && exit 1)
	@test -f src/sample_app/calculator.py || (echo "❌ Missing src/sample_app/calculator.py" && exit 1)
	@test -f tests/test_calculator.py || (echo "❌ Missing tests/test_calculator.py" && exit 1)
	@test -f pyproject.toml || (echo "❌ Missing pyproject.toml" && exit 1)
	@test -f requirements.txt || (echo "❌ Missing requirements.txt" && exit 1)
	@echo "✅ File structure verified"
	
	@echo "Checking Python environment..."
	@python --version || (echo "❌ Python not available" && exit 1)
	@echo "✅ Python environment verified"
	
	@echo "Checking dependencies..."
	@pip list | grep -E "(pytest|flake8|mypy|bandit)" || (echo "⚠️ Some development dependencies may be missing" && echo "Run 'make install' to install them")
	
	@echo "🎉 Verification completed successfully!"
