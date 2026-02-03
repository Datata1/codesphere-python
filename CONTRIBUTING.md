# Contributing to codesphere-python

First off, thank you for considering contributing to our project! We welcome any contributions, from fixing bugs and improving documentation to submitting new features.

---

## How Can I Contribute?

* **Reporting Bugs**: If you find a bug, please open a **GitHub Issue** and provide as much detail as possible, including steps to reproduce it.
* **Suggesting Enhancements**: If you have an idea for a new feature or an improvement, open a **GitHub Issue** to discuss it. This lets us coordinate our efforts and prevent duplicated work.
* **Pull Requests**: If you're ready to contribute code, documentation, or tests, you can open a Pull Request.

---

## Development Setup

To get your local development environment set up, please follow these steps:

1.  **Fork the repository** on GitHub.
2.  **Clone your forked repository** to your local machine:
    ```bash
    git clone https://github.com/YOUR_USERNAME/codesphere-python.git
    cd codesphere-python
    ```
3.  **Set up the project and install dependencies.** We use `uv` for package management. The following command will create a virtual environment and install all necessary dependencies for development:
    ```bash
    make install
    ```
4.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```
5.  **Set up environment variables for integration tests** (optional but recommended):
    ```bash
    cp .env.example .env
    # Edit .env and add your CS_TOKEN
    ```

You are now ready to start developing!

---

## Contribution Workflow

1.  **Create a new branch** for your changes. Please use a descriptive branch name.
    ```bash
    # Example for a new feature:
    git checkout -b feature/my-new-feature

    # Example for a bug fix:
    git checkout -b fix/bug-description
    ```
2.  **Make your code changes.** Write clean, readable code and add comments where necessary.
3.  **Format and lint your code** before committing to ensure it meets our style guidelines.
    ```bash
    make format
    make lint
    ```
4.  **Run the tests** to ensure that your changes don't break existing functionality.
    ```bash
    make test              # Run unit tests
    make test-integration  # Run integration tests (requires CS_TOKEN)
    ```
5.  **Commit your changes.** We follow the **[Conventional Commits](https://www.conventionalcommits.org/)** specification. You can use our commit command, which will guide you through the process:
    ```bash
    make commit
    ```
6.  **Push your changes** to your forked repository.
    ```bash
    git push origin feature/my-new-feature
    ```
7.  **Open a Pull Request** from your fork to our `main` branch. Please provide a clear title and description for your changes, linking to any relevant issues.

---

## Testing Guidelines

We maintain two types of tests: **unit tests** and **integration tests**. When contributing, please ensure appropriate test coverage for your changes.

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures for unit tests
├── core/                    # Tests for core SDK infrastructure
├── resources/               # Tests for resource implementations
│   ├── metadata/
│   ├── team/
│   └── workspace/
└── integration/             # Integration tests (real API calls)
    ├── conftest.py          # Integration test fixtures
    ├── test_domains.py
    ├── test_env_vars.py
    ├── test_metadata.py
    ├── test_teams.py
    └── test_workspaces.py
```

### Unit Tests

Unit tests mock HTTP responses and test SDK logic in isolation. They are fast and don't require API credentials.

**When to add unit tests:**
- Adding new Pydantic models or schemas
- Adding new API operations
- Modifying core handler logic
- Adding utility functions

**Example unit test pattern:**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_workspace_get():
    """Should fetch a workspace by ID."""
    mock_client = MagicMock()
    mock_client.request = AsyncMock(return_value=MagicMock(
        json=lambda: {"id": 123, "name": "test-ws", ...},
        raise_for_status=lambda: None
    ))
    
    resource = WorkspacesResource()
    resource._http_client = mock_client
    
    result = await resource.get(workspace_id=123)
    
    assert result.id == 123
    assert result.name == "test-ws"
```

### Integration Tests

Integration tests run against the real Codesphere API and verify end-to-end functionality. They require valid API credentials.

**When to add integration tests:**
- Adding new API endpoints
- Modifying request/response handling
- Changing how data is serialized/deserialized

**Running integration tests:**

```bash
# Set up credentials
export CS_TOKEN=your-api-token
# Or use a .env file
cp .env.example .env

# Run integration tests
make test-integration
```

**Environment variables for integration tests:**

| Variable | Required | Description |
|----------|----------|-------------|
| `CS_TOKEN` | Yes | Your Codesphere API token |
| `CS_TEST_TEAM_ID` | No | Specific team ID for tests |
| `CS_TEST_DC_ID` | No | Datacenter ID (defaults to 1) |

**Example integration test pattern:**

```python
import pytest
from codesphere import CodesphereSDK

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

class TestMyResourceIntegration:
    """Integration tests for MyResource endpoints."""

    async def test_list_resources(self, sdk_client: CodesphereSDK):
        """Should retrieve a list of resources."""
        resources = await sdk_client.my_resource.list()
        
        assert isinstance(resources, list)
        assert len(resources) > 0

    async def test_create_and_delete_resource(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        """Should create and delete a resource."""
        # Create
        resource = await sdk_client.my_resource.create(name="test")
        
        try:
            assert resource.name == "test"
        finally:
            # Always cleanup
            await resource.delete()
```

**Integration test fixtures** (available in `tests/integration/conftest.py`):

- `sdk_client` - A configured SDK client for each test
- `test_team_id` - The team ID to use for testing
- `test_workspace` - A pre-created test workspace
- `test_workspaces` - List of test workspaces (created at session start)

### Test Requirements for Pull Requests

1. **New features** must include both unit tests and integration tests
2. **Bug fixes** should include a test that reproduces the bug
3. **Schema changes** require unit tests validating serialization/deserialization
4. **All tests must pass** before a PR can be merged

---

## Pull Request Guidelines

* Ensure all tests and CI checks are passing.
* If you've added new functionality, please add corresponding tests (both unit and integration).
* Keep your PR focused on a single issue or feature.
* A maintainer will review your PR and provide feedback.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please be respectful and considerate in all your interactions.