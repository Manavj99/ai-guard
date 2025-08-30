.PHONY: help install test lint type-check security coverage clean docker docker-run

help:  ## Show this help message
	@echo "AI-Guard Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install -e .

test:  ## Run tests with coverage
	pytest -v --cov=src --cov-report=term-missing

lint:  ## Run flake8 linting
	flake8 src tests

type-check:  ## Run mypy type checking
	mypy src

security:  ## Run security scans
	bandit -r src -c .bandit

coverage:  ## Run tests and generate coverage report
	pytest --cov=src --cov-report=html --cov-report=xml

clean:  ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

all: lint type-check security test  ## Run all quality checks

ci:  ## Run CI checks (used by GitHub Actions)
	python -m src.ai_guard.analyzer --min-cov 80

docker:  ## Build Docker image
	docker build -t ai-guard:latest .

docker-run:  ## Run Docker container (scan current repo)
	docker run --rm -v "$(PWD)":/workspace ai-guard:latest --min-cov 80 --sarif /workspace/ai-guard.sarif
