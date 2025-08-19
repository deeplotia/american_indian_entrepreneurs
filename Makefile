.PHONY: help install install-dev test format lint type-check clean run setup

help: ## Show this help message
	@echo "American Indian Entrepreneurs - Development Commands"
	@echo "=================================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Quick setup with uv
	@echo "🚀 Setting up project..."
	python setup.py

install: ## Install core dependencies
	@echo "📦 Installing core dependencies..."
	uv sync

install-dev: ## Install development dependencies
	@echo "🔧 Installing development dependencies..."
	uv sync --extra dev

install-ml: ## Install machine learning dependencies
	@echo "🤖 Installing ML dependencies..."
	uv sync --extra ml

install-all: ## Install all dependencies
	@echo "📚 Installing all dependencies..."
	uv sync --all-extras

test: ## Run tests
	@echo "🧪 Running tests..."
	uv run pytest

test-pytest: ## Run tests with pytest
	@echo "🧪 Running pytest..."
	uv run pytest

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	uv run black src/
	uv run isort src/

lint: ## Lint code with flake8
	@echo "🔍 Linting code..."
	uv run flake8 src/

type-check: ## Type check with mypy
	@echo "🔍 Type checking..."
	uv run mypy src/

check: format lint type-check ## Run all code quality checks

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	rm -rf output/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

run: ## Run the main script
	@echo "🚀 Running main script..."
	uv run python -m src.run

run-test: ## Run with test limit (100 companies)
	@echo "🧪 Running with test limit..."
	python -c "from src.run import main; import sys; sys.exit(main())"

dev: install-dev ## Install dev dependencies and run tests
	@echo "🔧 Development setup complete"
	@echo "Run 'make test' to test the installation"
