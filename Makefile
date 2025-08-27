.PHONY: help install install-dev clean lint format test test-cov security docs pre-commit quality-gate build

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation targets
install: ## Install the package
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

# Cleaning targets
clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .tox/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Code quality targets
lint: ## Run all linting checks
	flake8 src tests scripts
	mypy src
	bandit -r src -c pyproject.toml

format: ## Format code with black and isort
	black src tests scripts
	isort src tests scripts

format-check: ## Check code formatting without making changes
	black --check --diff src tests scripts
	isort --check-only --diff src tests scripts

# Testing targets
test: ## Run tests sequentially
	python scripts/run_tests.py sequential

test-cov: ## Run tests with coverage
	python scripts/run_tests.py coverage

test-parallel: ## Run tests in parallel
	python scripts/run_tests.py parallel

test-parallel-cov: ## Run tests in parallel with coverage
	python scripts/run_tests.py parallel --coverage

test-performance: ## Run performance tests
	python scripts/run_tests.py performance

test-unit: ## Run unit tests only
	python scripts/run_tests.py sequential --markers "unit"

test-integration: ## Run integration tests only
	python scripts/run_tests.py sequential --markers "integration"

test-unit-parallel: ## Run unit tests in parallel
	python scripts/run_tests.py parallel --markers "unit"

test-integration-parallel: ## Run integration tests in parallel
	python scripts/run_tests.py parallel --markers "integration"

test-validate-parallel: ## Validate parallel test setup
	python scripts/run_tests.py validate

test-fast: ## Run tests in parallel (alias for test-parallel)
	python scripts/run_tests.py parallel

# Comprehensive testing targets with enhanced reporting
test-comprehensive: ## Run comprehensive test suite with detailed reporting
	python scripts/run_comprehensive_tests.py

test-comprehensive-parallel: ## Run comprehensive tests in parallel
	python scripts/run_comprehensive_tests.py --mode parallel

test-comprehensive-unit: ## Run comprehensive unit tests only
	python scripts/run_comprehensive_tests.py --markers unit

test-comprehensive-integration: ## Run comprehensive integration tests only
	python scripts/run_comprehensive_tests.py --markers integration

test-comprehensive-fast: ## Run comprehensive fast tests only
	python scripts/run_comprehensive_tests.py --markers "unit and fast" --mode parallel

test-comprehensive-baseline: ## Run tests and establish performance baselines
	python scripts/run_comprehensive_tests.py --baseline

test-comprehensive-validate: ## Validate comprehensive test environment
	python scripts/run_comprehensive_tests.py --validate-only

test-comprehensive-coverage-95: ## Run tests with 95% coverage threshold
	python scripts/run_comprehensive_tests.py --coverage-threshold 95

test-comprehensive-ci: ## Run comprehensive tests optimized for CI/CD
	python scripts/run_comprehensive_tests.py --mode parallel --markers "not slow" --no-artifacts

# Enhanced reporting targets with actionable insights
test-reporting: ## Run tests with enhanced reporting and actionable insights
	python scripts/run_comprehensive_reporting_tests.py

test-reporting-parallel: ## Run tests with enhanced reporting in parallel
	python scripts/run_comprehensive_reporting_tests.py --mode parallel

test-reporting-unit: ## Run unit tests with enhanced reporting
	python scripts/run_comprehensive_reporting_tests.py --markers unit

test-reporting-integration: ## Run integration tests with enhanced reporting
	python scripts/run_comprehensive_reporting_tests.py --markers integration

test-reporting-fast: ## Run fast tests with enhanced reporting
	python scripts/run_comprehensive_reporting_tests.py --markers "fast and unit" --mode parallel

test-reporting-ci: ## Run tests with CI/CD optimized reporting
	python scripts/run_comprehensive_reporting_tests.py --ci-optimized

test-reporting-coverage-95: ## Run tests with 95% coverage threshold and enhanced reporting
	python scripts/run_comprehensive_reporting_tests.py --coverage-threshold 95

test-reporting-debug: ## Run tests with debug mode and enhanced reporting
	python scripts/run_comprehensive_reporting_tests.py --debug

# Generate enhanced reports from existing test data
test-generate-reports: ## Generate enhanced reports from existing test data
	python scripts/enhanced_test_reporter.py

test-generate-reports-coverage: ## Generate reports from specific coverage data
	python scripts/enhanced_test_reporter.py --coverage-data test_reports/coverage/coverage.json

test-generate-reports-junit: ## Generate reports from JUnit XML data
	python scripts/enhanced_test_reporter.py --test-results test_reports/junit/junit.xml

test-reports: ## Generate test reports from last run
	@echo "Opening test reports..."
	@if [ -d "test_reports" ]; then \
		echo "Test reports available in: test_reports/"; \
		echo "- HTML Coverage: test_reports/coverage/html/index.html"; \
		echo "- Summary: test_reports/test_summary_*.md"; \
		echo "- Performance: test_reports/performance/performance_report_*.md"; \
	else \
		echo "No test reports found. Run 'make test-comprehensive' first."; \
	fi

test-reports-open: ## Open test reports in browser (macOS/Linux)
	@if [ -d "test_reports/coverage/html" ]; then \
		if command -v open >/dev/null 2>&1; then \
			open test_reports/coverage/html/index.html; \
		elif command -v xdg-open >/dev/null 2>&1; then \
			xdg-open test_reports/coverage/html/index.html; \
		else \
			echo "Cannot open browser. View reports at: test_reports/coverage/html/index.html"; \
		fi; \
	else \
		echo "No HTML coverage report found. Run 'make test-comprehensive' first."; \
	fi

test-clean-reports: ## Clean test reports directory
	rm -rf test_reports/
	@echo "Test reports cleaned."

# Security targets
security: ## Run security checks
	bandit -r src -c pyproject.toml
	safety check

# Documentation targets
docs: ## Build documentation
	@if [ -d "docs" ]; then \
		cd docs && sphinx-build -b html . _build/html; \
	else \
		echo "No docs directory found"; \
	fi

docs-serve: ## Serve documentation locally
	@if [ -d "docs" ]; then \
		cd docs && sphinx-autobuild --host 0.0.0.0 --port 8000 . _build/html; \
	else \
		echo "No docs directory found"; \
	fi

# Pre-commit targets
pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

# Quality gate target
quality-gate: ## Run complete quality gate checks
	@echo "Running quality gate checks..."
	@echo "1. Code formatting..."
	@$(MAKE) format-check
	@echo "2. Linting..."
	@$(MAKE) lint
	@echo "3. Security checks..."
	@$(MAKE) security
	@echo "4. Tests with coverage..."
	@$(MAKE) test-cov
	@echo "5. Pre-commit hooks..."
	@$(MAKE) pre-commit
	@echo "✅ All quality gate checks passed!"

# Build targets
build: ## Build package
	python -m build

build-check: ## Build and check package
	python -m build
	twine check dist/*

# Tox targets
tox: ## Run tox tests
	tox

tox-parallel: ## Run tox tests in parallel
	tox --parallel auto

# Development workflow targets
dev-setup: install-dev pre-commit-install ## Complete development setup
	@echo "Development environment setup complete!"

dev-check: format lint security test-cov ## Run all development checks
	@echo "All development checks passed!"

check-tools: ## Check if all quality tools are installed
	python scripts/check-tools.py

setup-dev: ## Run development setup script
	@if [ -f "scripts/setup-dev.sh" ]; then \
		./scripts/setup-dev.sh; \
	elif [ -f "scripts/setup-dev.bat" ]; then \
		scripts/setup-dev.bat; \
	else \
		echo "No setup script found"; \
	fi

quality-gate-script: ## Run quality gate validation script
	python scripts/quality-gate.py

# CI simulation
ci-local: clean dev-check build-check ## Simulate CI pipeline locally
	@echo "Local CI simulation complete!"

# Version management targets
version-current: ## Show current version
	python scripts/version_manager.py current

version-next: ## Calculate next version based on commits
	python scripts/version_manager.py next

version-bump: ## Bump version automatically based on commits
	python scripts/version_manager.py bump --tag

version-bump-major: ## Bump major version
	python scripts/version_manager.py bump --type major --tag

version-bump-minor: ## Bump minor version
	python scripts/version_manager.py bump --type minor --tag

version-bump-patch: ## Bump patch version
	python scripts/version_manager.py bump --type patch --tag

version-validate: ## Validate version consistency
	python scripts/version_manager.py validate

version-history: ## Show version history
	python scripts/version_manager.py history

version-analyze: ## Analyze commits for conventional commit compliance
	python scripts/version_manager.py analyze --verbose

# Changelog management targets
changelog-generate: ## Generate changelog entry for current version
	python scripts/changelog_generator.py generate $(shell python scripts/version_manager.py current --json | jq -r '.version')

changelog-validate: ## Validate CHANGELOG.md format
	python scripts/changelog_generator.py validate

changelog-release-notes: ## Generate release notes for current version
	python scripts/changelog_generator.py release-notes $(shell python scripts/version_manager.py current --json | jq -r '.version')

# Release preparation
release-check: clean quality-gate build-check version-validate changelog-validate ## Check if ready for release
	@echo "Release readiness check complete!"

release-prepare: ## Prepare for release (bump version, update changelog, and create tag)
	@echo "Preparing release..."
	@$(MAKE) version-bump
	@$(MAKE) changelog-generate
	@echo "Release preparation complete!"

release-notes: ## Generate release notes for the current version
	@$(MAKE) changelog-release-notes

# Milestone tracking targets
milestone-list: ## List all roadmap milestones
	python scripts/milestone_tracker.py list

milestone-update: ## Update milestone progress (requires VERSION and PROGRESS)
	@if [ -z "$(VERSION)" ] || [ -z "$(PROGRESS)" ]; then \
		echo "Usage: make milestone-update VERSION=v0.2.0 PROGRESS=50"; \
		exit 1; \
	fi
	python scripts/milestone_tracker.py update $(VERSION) $(PROGRESS) --update-roadmap

milestone-report: ## Generate milestone progress report
	python scripts/milestone_tracker.py report

milestone-roadmap-update: ## Update ROADMAP.md with current milestone status
	python scripts/milestone_tracker.py roadmap

# Release management targets
release-validate: ## Validate release readiness
	python scripts/prepare_release.py validate

release-version: ## Calculate next release version
	python scripts/prepare_release.py version

release-prepare-auto: ## Prepare release with automatic version bumping
	python scripts/prepare_release.py prepare

release-prepare-major: ## Prepare major release
	python scripts/prepare_release.py prepare --bump-type major

release-prepare-minor: ## Prepare minor release
	python scripts/prepare_release.py prepare --bump-type minor

release-prepare-patch: ## Prepare patch release
	python scripts/prepare_release.py prepare --bump-type patch

release-dry-run: ## Dry run of release preparation
	python scripts/prepare_release.py prepare --dry-run

release-push: ## Prepare and push release
	python scripts/prepare_release.py prepare --push