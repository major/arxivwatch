.PHONY: test lint typecheck check all clean

# Run all checks (test, lint, typecheck)
all: test lint typecheck

# Run tests with pytest
test:
	uv run pytest tests/ -v

# Run linting and auto-fix issues with ruff
lint:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

# Run type checking with pyright
typecheck:
	uv run pyright src/ tests/

# Convenience target for running all checks
check: all

# Clean up temporary files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Run the application
run:
	uv run python -m arxivwatch.main

# Show help
help:
	@echo "Available targets:"
	@echo "  all        - Run tests, linting, and type checking (default)"
	@echo "  test       - Run tests with pytest"
	@echo "  lint       - Lint and auto-fix code with ruff"
	@echo "  typecheck  - Run type checking with pyright"
	@echo "  check      - Alias for 'all'"
	@echo "  clean      - Remove temporary files"
	@echo "  run        - Run the application"
	@echo "  help       - Show this help message"