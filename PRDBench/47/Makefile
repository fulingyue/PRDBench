.PHONY: setup test lint format check clean

# ── Environment Setup ──────────────────────────────────────────────────────────
setup:
	@echo "==> Creating virtual environment..."
	python3 -m venv .venv
	@echo "==> Installing all dependencies from pyproject.toml..."
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	@echo "==> Setup complete. Activate with: source .venv/bin/activate"

# ── Testing ───────────────────────────────────────────────────────────────────
test:
	.venv/bin/pytest --cov=src --cov-report=term-missing --cov-fail-under=95

# ── Linting & Type Checking ───────────────────────────────────────────────────
format:
	.venv/bin/ruff format src/ tests/

lint:
	.venv/bin/ruff check src/ tests/
	.venv/bin/ruff format --check src/ tests/
	.venv/bin/mypy src/

# ── Full CI Check (lint + test) ───────────────────────────────────────────────
check: lint test

# ── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
