.PHONY: help install lint format test test-integration test-unit bump release pypi tree version changelog

.DEFAULT_GOAL := help

# ─── Helpers ──────────────────────────────────────────────────────────────────

CURRENT_VERSION = $(shell grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')

help: ## Shows a help message with all available commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ─── Setup ────────────────────────────────────────────────────────────────────

install: ## Sets up the development environment
	@echo ">>> Setting up the development environment..."
	@echo "1. Creating virtual environment with uv..."
	uv venv --python 3.12.9
	@echo "2. Installing all dependencies (including 'dev')..."
	uv pip install -e '.[dev]'
	@echo "3. Installing git hooks with pre-commit..."
	uv run pre-commit install --hook-type commit-msg --hook-type pre-commit --hook-type pre-push
	@echo "\n\033[0;32mSetup complete! Please activate the virtual environment with 'source .venv/bin/activate'.\033[0m"

# ─── Code Quality ────────────────────────────────────────────────────────────

lint: ## Checks code quality with ruff
	@echo ">>> Checking code quality with ruff..."
	uv run ruff check src --fix

format: ## Formats code with ruff
	@echo ">>> Formatting code with ruff..."
	uv run ruff format src

# ─── Testing ─────────────────────────────────────────────────────────────────

test: ## Runs all tests with pytest
	@echo ">>> Running all tests with pytest..."
	uv run pytest

test-unit: ## Runs only unit tests (excludes integration tests)
	@echo ">>> Running unit tests with pytest..."
	uv run pytest --ignore=tests/integration

test-integration: ## Runs integration tests (requires CS_TOKEN env var or .env file)
	@echo ">>> Running integration tests with pytest..."
	@if [ -f .env ]; then \
		echo "Loading environment from .env file..."; \
		set -a; . ./.env; set +a; \
	fi; \
	if [ -z "$${CS_TOKEN}" ]; then \
		echo "\033[0;33mWarning: CS_TOKEN not set. Create a .env file or export CS_TOKEN=your-api-token\033[0m"; \
		exit 1; \
	fi; \
	uv run pytest tests/integration -v --run-integration

# ─── Versioning & Release ────────────────────────────────────────────────────

version: ## Shows the current project version
	@echo "$(CURRENT_VERSION)"

bump: ## Bumps the version. Usage: make bump VERSION=0.5.0
	@if [ -z "$(VERSION)" ]; then \
		echo "\033[0;31mERROR: VERSION is required. Usage: make bump VERSION=0.5.0\033[0m"; \
		echo "  Current version: $(CURRENT_VERSION)"; \
		exit 1; \
	fi
	@echo ">>> Bumping version from $(CURRENT_VERSION) to $(VERSION)..."
	@sed -i '' 's/^version = ".*"/version = "$(VERSION)"/' pyproject.toml
	@echo "\033[0;32mVersion updated to $(VERSION) in pyproject.toml\033[0m"

changelog: ## Generates a changelog entry from git log since last tag. Usage: make changelog [VERSION=x.y.z]
	@NEW_VERSION=$${VERSION:-$(CURRENT_VERSION)}; \
	LAST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo ""); \
	DATE=$$(date +%Y-%m-%d); \
	echo ">>> Generating changelog for v$${NEW_VERSION} ($${DATE})..."; \
	TMPFILE=$$(mktemp); \
	echo "## v$${NEW_VERSION} ($${DATE})" > $$TMPFILE; \
	echo "" >> $$TMPFILE; \
	if [ -n "$$LAST_TAG" ]; then \
		FEATS=$$(git log $${LAST_TAG}..HEAD --pretty=format:"- %s" --grep="^feat" 2>/dev/null); \
		FIXES=$$(git log $${LAST_TAG}..HEAD --pretty=format:"- %s" --grep="^fix" 2>/dev/null); \
		REFACTORS=$$(git log $${LAST_TAG}..HEAD --pretty=format:"- %s" --grep="^refactor" 2>/dev/null); \
		OTHERS=$$(git log $${LAST_TAG}..HEAD --pretty=format:"- %s" --invert-grep --grep="^feat" --grep="^fix" --grep="^refactor" 2>/dev/null); \
	else \
		FEATS=$$(git log --pretty=format:"- %s" --grep="^feat" 2>/dev/null); \
		FIXES=$$(git log --pretty=format:"- %s" --grep="^fix" 2>/dev/null); \
		REFACTORS=$$(git log --pretty=format:"- %s" --grep="^refactor" 2>/dev/null); \
		OTHERS=""; \
	fi; \
	if [ -n "$$FEATS" ]; then echo "### Features\n" >> $$TMPFILE; echo "$$FEATS" >> $$TMPFILE; echo "" >> $$TMPFILE; fi; \
	if [ -n "$$FIXES" ]; then echo "### Fixes\n" >> $$TMPFILE; echo "$$FIXES" >> $$TMPFILE; echo "" >> $$TMPFILE; fi; \
	if [ -n "$$REFACTORS" ]; then echo "### Refactors\n" >> $$TMPFILE; echo "$$REFACTORS" >> $$TMPFILE; echo "" >> $$TMPFILE; fi; \
	if [ -n "$$OTHERS" ]; then echo "### Other\n" >> $$TMPFILE; echo "$$OTHERS" >> $$TMPFILE; echo "" >> $$TMPFILE; fi; \
	if [ -f CHANGELOG.md ]; then \
		cat CHANGELOG.md >> $$TMPFILE; \
	fi; \
	mv $$TMPFILE CHANGELOG.md; \
	echo "\033[0;32mChangelog updated.\033[0m"

release: ## Bumps version, updates changelog, commits, tags, and pushes. Usage: make release VERSION=0.5.0
	@if [ -z "$(VERSION)" ]; then \
		echo "\033[0;31mERROR: VERSION is required. Usage: make release VERSION=0.5.0\033[0m"; \
		echo "  Current version: $(CURRENT_VERSION)"; \
		exit 1; \
	fi
	@echo ">>> Starting release v$(VERSION)..."
	@# Guard: ensure working tree is clean (except for staged changes)
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "\033[0;33mWarning: You have uncommitted changes. Please commit or stash them first.\033[0m"; \
		git status --short; \
		exit 1; \
	fi
	@# Guard: ensure we are on main branch
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$BRANCH" != "main" ]; then \
		echo "\033[0;33mWarning: You are on branch '$$BRANCH', not 'main'. Continue? [y/N]\033[0m"; \
		read -r CONFIRM; \
		if [ "$$CONFIRM" != "y" ] && [ "$$CONFIRM" != "Y" ]; then \
			echo "Aborted."; \
			exit 1; \
		fi; \
	fi
	@# Guard: ensure tag does not already exist
	@if git rev-parse "v$(VERSION)" >/dev/null 2>&1; then \
		echo "\033[0;31mERROR: Tag v$(VERSION) already exists.\033[0m"; \
		exit 1; \
	fi
	@# Step 1: Bump version in pyproject.toml
	$(MAKE) bump VERSION=$(VERSION)
	@# Step 2: Update CHANGELOG.md
	$(MAKE) changelog VERSION=$(VERSION)
	@# Step 3: Commit and tag
	@echo ">>> Committing release..."
	git add pyproject.toml CHANGELOG.md
	git commit -m "release: v$(VERSION)"
	git tag -a "v$(VERSION)" -m "Release $(VERSION)"
	@# Step 4: Push commit and tag
	@echo ">>> Pushing to remote..."
	git push --follow-tags
	@echo "\n\033[0;32m✅ Released v$(VERSION). GitHub Actions will publish to PyPI and create the GitHub Release.\033[0m"

# ─── Publishing ──────────────────────────────────────────────────────────────

pypi: ## Builds and publishes to PyPI (usually called by CI)
	@echo "\n>>> Building package for distribution..."
	uv build
	@echo "\n>>> Publishing to PyPI..."
	uv publish
	@echo "\n\033[0;32mPyPI release complete!\033[0m"

# ─── Utilities ───────────────────────────────────────────────────────────────

tree: ## Shows filetree in terminal without uninteresting files
	tree -I "*.pyc|*.lock"
