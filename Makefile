# Shortcuts so nobody has to remember long commands.
# Usage: make <target>.  (Windows: run inside WSL2.)
PY ?= python

.PHONY: help setup format lint typecheck test check clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup:  ## Install the package with dev tools and git hooks
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"
	pre-commit install

format:  ## Auto-format code
	ruff format .
	ruff check --fix .

lint:  ## Check style without changing files
	ruff format --check .
	ruff check .

typecheck:  ## Static type check
	mypy src

test:  ## Run tests with coverage
	pytest --cov --cov-report=term-missing

check: lint typecheck test  ## Everything CI runs

clean:  ## Remove caches
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov build dist *.egg-info
