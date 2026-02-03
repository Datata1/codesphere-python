# Copilot Instructions for Codesphere Python SDK

## Project Context

This repository contains the **Codesphere Python SDK**, an official asynchronous Python client for the [Codesphere Public API](https://codesphere.com/api/swagger-ui/). It provides a high-level, type-safe interface for managing Codesphere resources including Teams, Workspaces, Domains, Environment Variables, and Metadata.

The SDK follows a resource-based architecture where API operations are defined declaratively and executed through a centralized handler system.

## Project Structure

```
src/codesphere/
├── __init__.py           # Public API exports
├── client.py             # Main SDK entry point (CodesphereSDK)
├── config.py             # Settings via pydantic-settings
├── exceptions.py         # Custom exception classes
├── http_client.py        # Async HTTP client wrapper (APIHttpClient)
├── utils.py              # Utility functions
├── core/                 # Core SDK infrastructure
│   ├── base.py           # Base classes (ResourceBase, CamelModel, ResourceList)
│   ├── handler.py        # API operation executor (_APIOperationExecutor, APIRequestHandler)
│   └── operations.py     # APIOperation definition and AsyncCallable type
└── resources/            # API resource implementations
    ├── metadata/         # Datacenters, Plans, Images
    ├── team/             # Teams and nested Domains
    │   └── domain/       # Domain management (schemas, operations, manager)
    └── workspace/        # Workspaces and nested resources
        ├── envVars/      # Environment variables management
        ├── landscape/    # (Placeholder)
        └── pipeline/     # (Placeholder)

tests/                    # Test files mirroring src structure
├── conftest.py           # Shared unit test fixtures
├── core/                 # Core infrastructure tests
├── resources/            # Resource unit tests
└── integration/          # Integration tests (real API)
    ├── conftest.py       # Integration fixtures & workspace setup
    ├── test_domains.py
    ├── test_env_vars.py
    ├── test_metadata.py
    ├── test_teams.py
    └── test_workspaces.py

examples/                 # Usage examples organized by resource type
```

## Coding Guidelines

### General Principles

- **Async-First**: All API operations MUST be async. Use `async/await` syntax consistently.
- **Type Hints**: Always provide complete type annotations for function parameters, return values, and class attributes.
- **Pydantic Models**: Use Pydantic `BaseModel` for all data structures. Prefer `CamelModel` for API payloads to handle camelCase conversion.

### Naming Conventions

- **Variables/Functions**: Use `snake_case` (e.g., `workspace_id`, `list_datacenters`)
- **Classes**: Use `PascalCase` (e.g., `WorkspaceCreate`, `APIHttpClient`)
- **Constants/Operations**: Use `UPPER_SNAKE_CASE` with leading underscore for internal operations (e.g., `_LIST_BY_TEAM_OP`)
- **Private Attributes**: Prefix with underscore (e.g., `_http_client`, `_token`)

### Resource Pattern

When adding new API resources, follow this structure:

1. **schemas.py**: Define Pydantic models for Create, Base, Update, and the main resource class
2. **operations.py**: Define `APIOperation` instances for each endpoint
3. **resources.py**: Create the resource class extending `ResourceBase` with operation fields
4. **__init__.py**: Export public classes

```python
# Example operation definition
_GET_OP = APIOperation(
    method="GET",
    endpoint_template="/resources/{resource_id}",
    response_model=ResourceModel,
)

# Example resource method
async def get(self, resource_id: int) -> ResourceModel:
    return await self.get_op(resource_id=resource_id)
```

### Model Guidelines

- Extend `CamelModel` for API request/response models (automatic camelCase aliasing)
- Extend `_APIOperationExecutor` for models that can perform operations on themselves
- Use `Field(default=..., exclude=True)` for operation callables
- Use `@cached_property` for lazy-loaded sub-managers (e.g., `workspace.env_vars`)

```python
class Workspace(WorkspaceBase, _APIOperationExecutor):
    delete_op: AsyncCallable[None] = Field(default=_DELETE_OP, exclude=True)
    
    async def delete(self) -> None:
        await self.delete_op()
```

### Error Handling

- Raise `httpx.HTTPStatusError` for HTTP errors (handled by `APIHttpClient`)
- Raise `RuntimeError` for SDK misuse (e.g., accessing resources without context manager)
- Use custom exceptions from `exceptions.py` for SDK-specific errors

### Code Style

- Line length: 88 characters (Ruff/Black standard)
- Indentation: 4 spaces
- Quotes: Double quotes for strings
- Imports: Group stdlib, third-party, and local imports

---

## Testing Guidelines

When adding features or making changes, appropriate tests are **required**. The SDK uses two types of tests:

### Unit Tests

Located in `tests/` (excluding `tests/integration/`). These mock HTTP responses and test SDK logic in isolation.

**When to write unit tests:**
- New Pydantic models or schemas
- New API operations
- Core handler or utility logic changes

**Unit test patterns:**

```python
import pytest
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

# Use @dataclass for parameterized test cases
@dataclass
class WorkspaceTestCase:
    name: str
    workspace_id: int
    expected_name: str

@pytest.mark.asyncio
@pytest.mark.parametrize("case", [
    WorkspaceTestCase(name="basic", workspace_id=123, expected_name="test-ws"),
])
async def test_workspace_get(case: WorkspaceTestCase):
    """Should fetch a workspace by ID."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": case.workspace_id, "name": case.expected_name}
    
    # Test implementation...
```

### Integration Tests

Located in `tests/integration/`. These run against the real Codesphere API.

**When to write integration tests:**
- New API endpoints (CRUD operations)
- Changes to request/response serialization
- Schema field changes (detect API contract changes early)

**Integration test patterns:**

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

    async def test_create_and_delete(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        """Should create and delete a resource."""
        resource = await sdk_client.my_resource.create(name="test")
        
        try:
            assert resource.name == "test"
        finally:
            # Always cleanup created resources
            await resource.delete()
```

**Available integration test fixtures** (from `tests/integration/conftest.py`):

| Fixture | Scope | Description |
|---------|-------|-------------|
| `sdk_client` | function | Fresh SDK client for each test |
| `session_sdk_client` | session | Shared SDK client for setup/teardown |
| `test_team_id` | session | Team ID for testing |
| `test_workspace` | session | Single pre-created workspace |
| `test_workspaces` | session | List of 2 test workspaces |
| `integration_token` | session | The API token (from `CS_TOKEN`) |

**Environment variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `CS_TOKEN` | Yes | Codesphere API token |
| `CS_TEST_TEAM_ID` | No | Specific team ID (defaults to first team) |
| `CS_TEST_DC_ID` | No | Datacenter ID (defaults to 1) |

### Running Tests

```bash
make test              # Run unit tests only
make test-unit         # Run unit tests only (explicit)
make test-integration  # Run integration tests (requires CS_TOKEN)
```

### Test Requirements Checklist

When submitting a PR, ensure:

- [ ] **New endpoints** have integration tests covering all operations
- [ ] **New models** have unit tests for serialization/deserialization
- [ ] **Bug fixes** include a test that reproduces the issue
- [ ] **All tests pass** locally before pushing

---

## Development Commands

```bash
make install           # Set up development environment
make lint              # Run Ruff linter
make format            # Format code with Ruff
make test              # Run unit tests
make test-unit         # Run unit tests (excludes integration)
make test-integration  # Run integration tests
make commit            # Guided commit with Commitizen
```