# Codesphere SDK - AI Instructions

## Architecture & Core
- **Async-First:** All I/O operations MUST be `async/await`.
- **Base Classes:**
  - Models: Use `core.base.CamelModel` (handles camelCase API conversion).
  - Resources: Inherit from `ResourceBase` + `_APIOperationExecutor`.
- **HTTP:** Use `APIHttpClient` (wraps httpx). Raise `httpx.HTTPStatusError` for API errors.

## Project Structure
- `src/codesphere/core/`: Base classes & handlers.
- `src/codesphere/resources/`: Resource implementations (follow `schemas.py`, `operations.py`, `resources.py` pattern).
- `tests/integration/`: Real API tests (require `CS_TOKEN`).
- `tests/unit/`: Mocked logic tests.

## Resource Implementation Pattern
When adding resources, strictly follow this pattern:

1. **`schemas.py`**: Define Pydantic models (inherit `CamelModel`).
2. **`operations.py`**: Define `APIOperation` constants.
   ```python
   _GET_OP = APIOperation(method="GET", endpoint_template="/res/{id}", response_model=ResModel)
   ```
3. **`resources.py`**: Implementation logic.
   ```python
   class MyResource(ResourceBase, _APIOperationExecutor):
       # Operation callable (exclude from model dump)
       delete_op: AsyncCallable[None] = Field(default=_DELETE_OP, exclude=True)
       
       async def delete(self) -> None:
           await self.delete_op()
   ```

## Testing Rules
- **Unit Tests (`tests/`):** MUST mock all HTTP calls (`unittest.mock.AsyncMock`).
- **Integration Tests (`tests/integration/`):**
  - Use `pytest.mark.integration`.
  - Use provided fixtures: `sdk_client` (fresh client), `test_team_id`, `test_workspace`.
  - **Cleanup:** Always delete created resources in a `try...finally` block.

## Key Fixtures & Env Vars
| Fixture | Scope | Description |
|---|---|---|
| `sdk_client` | func | Fresh `CodesphereSDK` instance. |
| `test_team_id` | session | ID from `CS_TEST_TEAM_ID` (or default). |
| `integration_token` | session | Token from `CS_TOKEN`. |

## Style & Naming
- **Classes:** PascalCase (`WorkspaceCreate`).
- **Vars:** snake_case.
- **Internal Ops:** UPPER_SNAKE (`_LIST_OP`).
- **Private:** Leading underscore (`_http_client`).
- **Typing:** Strict type hints required.