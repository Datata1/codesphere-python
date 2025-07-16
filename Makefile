.PHONY: help install commit lint format test bump

.DEFAULT_GOAL := help

help: ## Shows a help message with all available commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Sets up the development environment
	@echo ">>> Setting up the development environment..."
	@echo "1. Creating virtual environment with uv..."
	uv venv
	@echo "2. Installing all dependencies (including 'dev')..."
	uv pip install -e '.[dev]'
	@echo "3. Installing git hooks with pre-commit..."
	pre-commit install --hook-type commit-msg --hook-type pre-commit --hook-type pre-push
	@echo "\n\033[0;32mSetup complete! Please activate the virtual environment with 'source .venv/bin/activate'.\033[0m"

commit: ## Starts Commitizen for a guided commit message
	@echo ">>> Starting Commitizen for a guided commit message..."
	@if git diff --cached --quiet; then \
		echo "\033[0;33mWarning: No changes added to commit (please use 'git add ...' first).\033[0m"; \
		exit 1; \
	fi
	uv run cz commit
	uv run cz bump --changelog --allow-no-commit


lint: ## Checks code quality with ruff
	@echo ">>> Checking code quality with ruff..."
	uv run ruff check src tests

format: ## Formats code with ruff
	@echo ">>> Formatting code with ruff..."
	uv run ruff format src tests

test: ## Runs tests with pytest
	@echo ">>> Running tests with pytest..."
	uv run pytest

release: ## Pushes a new tag and release
	@echo ">>> Starting release process..."
	git config --global push.followTags true

	@echo "\n>>> Verifying tag and pushing to remote..."
	export VERSION=$$(uv run cz version --project); \
	if [ -z "$${VERSION}" ]; then \
		echo "\033[0;31mERROR: Could not determine version using 'cz version --project'.\033[0m"; \
		exit 1; \
	fi; \
	echo "--- Found project version: v$${VERSION} ---"; \
	if git rev-parse "v$${VERSION}" >/dev/null 2>&1; then \
		echo "--- Verified local tag v$${VERSION} exists. ---"; \
	else \
		echo "\033[0;31mERROR: Git tag v$${VERSION} was not found! Please check for errors.\033[0m"; \
		exit 1; \
	fi; \
	echo "--- Pushing commit and tag to remote... ---"; \
	git tag -d v$${VERSION}; \
	git tag -a v$${VERSION} -m "Release $${VERSION}"; \
	git push --follow-tags; \
	echo "\n\033[0;32m✅ SUCCESS: Tag v$${VERSION} pushed to GitHub. The release workflow has been triggered.\033[0m"

pypi: ## publishes to PyPI
	@echo "\n>>> Building package for distribution..."
	uv build
	@echo "\n>>> Publishing to PyPI..."
	uv publish
	@echo "\n\033[0;32mPyPI release complete! The GitHub Action will now create the GitHub Release.\033[0m"