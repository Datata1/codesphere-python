# 03 — Constructor-injectable config, lazy settings, single close path

**Priority:** P1
**Depends on:** 01; mostly parallel to 02 (one noted overlap)

## Problem

1. **`import codesphere` crashes without `CS_TOKEN`.** `src/codesphere/config.py:20` runs
   `settings = Settings()` at module import and `token: SecretStr` (`config.py:13`) is
   required, so a bare import raises a raw pydantic `ValidationError`. The purpose-built
   `AuthenticationError` in `exceptions.py` (whose message even says to set `CS_TOKEN`) is
   **never raised anywhere** — dead code.

2. **No per-client configuration.** `CodesphereSDK.__init__` (`client.py:12-16`) takes no
   arguments and `APIHttpClient.__init__` reads the token from the global `settings`
   (`http_client.py:16`). Two clients with different tokens in one process are impossible;
   pointing at a staging URL requires env mutation before import.

3. **`CS_BASE_URL` is dead.** `http_client.py:15-17`:
   ```python
   def __init__(self, base_url: str = "https://codesphere.com/api"):
       self._base_url = base_url or str(settings.base_url)
   ```
   The parameter default is a non-empty string, so `settings.base_url` is only consulted if a
   caller passes `""` — and `client.py:13` calls `APIHttpClient()` with no args. The env var
   and the duplicated literal can silently disagree.

4. Assorted lifecycle/typing debris:
   - `http_client.py:29-30` `setattr`s dynamic `get/post/...` verb methods — untyped,
     invisible to IDEs, and unused (the handler always calls `.request`).
   - Duplicate payload serialization: the handler dumps `BaseModel` payloads AND
     `http_client.request` re-dumps (`http_client.py:62-63`).
   - `client.py` has two divergent close paths: `close()` (`:21-22`) discards exception info
     while `__aexit__` (`:28-29`) bypasses `close()` entirely.
   - `config.py:14` `base_url: HttpUrl = "https://codesphere.com/api"` — a `str` default on an
     `HttpUrl` field (runtime-coerced, statically wrong).

## Approach

1. **Make settings lazy.** Delete module-level `settings = Settings()`. Make
   `token: SecretStr | None = None`. `Settings()` is constructed inside the client path only
   (a small `Settings.load()` or plain construction in `CodesphereSDK.__init__`). Fix the
   `base_url` default to a proper `HttpUrl` value so the field type-checks.

2. **Constructor injection with explicit resolution order.**
   ```python
   class CodesphereSDK:
       def __init__(
           self,
           token: str | SecretStr | None = None,
           base_url: str | None = None,
           timeout: httpx.Timeout | None = None,
           http_client: APIHttpClient | None = None,   # escape hatch for tests/advanced use
       ) -> None: ...
   ```
   Resolution: explicit argument → `CS_*` env via `Settings()` → built-in default. A missing
   token raises `AuthenticationError` **at construction** (finally using the existing
   exception and its message).

3. **Make `APIHttpClient` a dumb transport.**
   `def __init__(self, *, token: SecretStr, base_url: str, timeout: httpx.Timeout)` — no
   `settings` access inside; the SDK resolves config, the transport receives it. Delete the
   `setattr` verb loop. Remove the `BaseModel` re-dump from `request` so serialization is
   owned solely by `execute_operation` (from ticket 02 — if 03 lands first, keep the re-dump
   until 02 merges, then delete it there).

4. **One close path.** `__aexit__` delegates to a single `close(exc_type=None, ...)`;
   `CodesphereSDK.close()` and `__aexit__` both route through it.

5. Update README/examples for `CodesphereSDK(token=...)` (env-only usage keeps working
   unchanged).

## Breaking changes

- `import codesphere` no longer raises when `CS_TOKEN` is unset — the failure moves to
  `CodesphereSDK()` construction and changes type from pydantic `ValidationError` to
  `codesphere.AuthenticationError`. Anyone catching the pydantic error at import time (nobody
  should be) is affected. CHANGELOG entry: behavior fix.
- `APIHttpClient.__init__` signature changes (internal; ticket 02 declares `core`/transport
  internals private).

## Acceptance criteria

- [ ] `env -i python -c "import codesphere"` succeeds (no env vars needed to import).
- [ ] `CodesphereSDK()` without a token (arg or env) raises `AuthenticationError`.
- [ ] `CodesphereSDK(token="x", base_url="http://localhost:8000")` sends requests to the
      custom URL (respx test); `CS_BASE_URL` env var is honored when no arg is given (test).
- [ ] Two SDK instances with different tokens send different `Authorization` headers (test).
- [ ] No dynamic `setattr` verb methods; exactly one payload-serialization site; exactly one
      close path (`grep` + tests).
- [ ] `config.py`, `http_client.py`, `client.py` removed from the ty ratchet; `uv run ty check`
      passes.
