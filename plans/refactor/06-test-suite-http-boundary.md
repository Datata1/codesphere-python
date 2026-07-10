# 06 — Test at the HTTP boundary (respx); cover the untested core modules

**Priority:** P2
**Depends on:** 02, 03

## Problem

- Unit tests mock at the dispatch boundary — e.g.
  `landscape_manager._execute_operation = AsyncMock()`
  (`tests/resources/workspace/landscape/test_pipeline.py:94`) — so real request construction,
  URL/path formatting, auth header injection, error mapping, and response deserialization are
  never exercised by unit tests. Only the live-credential integration suite (gated to the
  upstream repo's secrets) touches that path.
- **Zero dedicated unit tests** exist for `exceptions.py` (10 exported error types, including
  the `raise_for_status` status→exception mapping and `Retry-After` parsing), `config.py`,
  `http_client.py`, and `utils.py`.

## Approach

1. Add `respx` to the dev group. Shared fixture (e.g. in `tests/conftest.py`):
   `mock_api` — a `respx.mock` router bound to the SDK's base URL, plus an `sdk` fixture
   yielding an opened `CodesphereSDK(token="test-token", base_url="https://test.local/api")`
   (uses ticket 03's constructor injection).

2. **Exception matrix** (`tests/test_exceptions.py`): for each mapped status
   (400, 401, 403, 404, 409, 422, 429, 5xx) assert the raised class, `message`, `status_code`,
   parsed `errors`, and `RateLimitError.retry_after` from the `Retry-After` header; plus
   non-JSON error bodies and the httpx timeout/connect-error → `TimeoutError`/`NetworkError`
   mapping in `http_client.request`.

3. **Executor behavior** (`tests/core/test_execute_operation.py`), asserting on the *real*
   outgoing request via respx: endpoint template formatting from explicit path params
   (missing param → clear error), `input_model` validation rejecting bad payloads before any
   request, `data={}` sending an empty JSON object (falsy-body regression from ticket 02),
   `APIOperation[None]` returning `None` without parsing, `ResourceList` items receiving the
   injected client (calling a method on a returned entity hits the mock).

4. **Config resolution** (`tests/test_config.py`): arg > env > default precedence for token
   and base_url; import without env vars; `AuthenticationError` on missing token; two SDKs →
   two Authorization headers (from ticket 03's criteria).

5. **Migration policy:** new tests are respx-only; existing `AsyncMock(_execute...)` tests are
   converted opportunistically whenever their module is touched by tickets 02/04/05 — no
   big-bang rewrite. Add a short note to CONTRIBUTING.md: unit tests for request/response
   behavior mock the transport (respx), not SDK internals.

## Breaking changes

None (tests and dev dependencies only).

## Acceptance criteria

- [ ] Line coverage > 90% for `exceptions.py`, `config.py`, `http_client.py`, and the executor
      module (measured with ticket 01's fixed coverage config).
- [ ] No **new** test mocks `_execute`/`_execute_operation` or SDK-internal methods for
      request/response behavior.
- [ ] The exception matrix covers every exception class exported from `codesphere.__init__`.
- [ ] Suite runs offline (no `CS_*` env needed) and passes in CI.
