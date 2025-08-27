# AI-Guard: Smart Code Quality Gatekeeper

**Goal:** Stop risky PRs (especially AI-generated ones) from merging by enforcing quality, security, and test gates — and by auto-generating targeted tests for changed code.

## Why
Modern teams ship faster with AI. AI-Guard keeps quality high with automated, opinionated gates: lint, types, security, coverage, and speculative tests.

## Features
- Linting (flake8), typing (mypy)
- Security scan (bandit)
- Coverage threshold (default 80%)
- Speculative test generation for changed files
- Single-command CI integration (GitHub Actions)

## Quickstart
```bash
pip install -r requirements.txt
pytest -q
```

Push a PR: the GitHub Action runs AI-Guard and fails the check if gates aren't met.

## Roadmap

* Parse PR diffs to target functions precisely
* LLM-assisted test synthesis (opt-in)
* SARIF output + PR annotations
* Language adapters (JS/TS, Go, Rust)
