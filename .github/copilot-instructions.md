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
    return await self.get_op(data=resource_id)
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

### Testing

- Use `pytest.mark.asyncio` for async tests
- Use `@dataclass` for test case definitions with parametrization
- Mock `httpx.AsyncClient` for HTTP request testing
- Test files should mirror the source structure in `tests/`

### Code Style

- Line length: 88 characters (Ruff/Black standard)
- Indentation: 4 spaces
- Quotes: Double quotes for strings
- Imports: Group stdlib, third-party, and local imports

### Development Commands

```bash
make install    # Set up development environment
make lint       # Run Ruff linter
make format     # Format code with Ruff
make test       # Run pytest
make commit     # Guided commit with Commitizen
```