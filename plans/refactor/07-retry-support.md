# 07 — Opt-in retry with backoff, honoring `Retry-After`

**Priority:** P3
**Depends on:** 03 (constructor injection), 06 (respx harness for tests)

## Problem

The SDK parses `Retry-After` into `RateLimitError.retry_after` (`exceptions.py`), and until
ticket 01 it even shipped `aiohttp-retry` as a dependency — but **no retry logic exists
anywhere**. Nothing consumes `retry_after`; a 429 or a transient 503 always surfaces
immediately to the caller. The feature is implied but absent.

## Approach

1. **Config object** (in `config.py` or a new `retry.py`):
   ```python
   @dataclass(frozen=True, slots=True)
   class RetryConfig:
       max_retries: int = 0                      # 0 = disabled (default: zero behavior change)
       backoff_factor: float = 0.5               # sleep = backoff_factor * 2**attempt, jittered
       retry_statuses: frozenset[int] = frozenset({429, 502, 503, 504})
       retry_methods: frozenset[str] = frozenset({"GET", "HEAD", "PUT", "DELETE"})  # idempotent only
   ```

2. **Wire-through:** `CodesphereSDK(..., retry: RetryConfig | None = None)` → passed to
   `APIHttpClient`.

3. **Implementation:** a loop in `APIHttpClient.request` around the send + `raise_for_status`:
   - retry on a response whose status is in `retry_statuses` **and** whose method is in
     `retry_methods` (POST retried only if the caller opts in via `retry_methods`), and on
     `httpx.TimeoutException`/`httpx.ConnectError`;
   - sleep = `Retry-After` header value when present (seconds or HTTP-date), else exponential
     backoff with jitter, via `asyncio.sleep`;
   - after `max_retries` attempts, raise the same exception the non-retry path would
     (`RateLimitError`, `NetworkError`, …) so error handling is unchanged;
   - `log.debug` each retry with attempt count and delay.

   Keep it a plain loop — do not reintroduce a retry dependency; httpx has no native retry and
   the logic is ~30 lines.

## Breaking changes

None. Default `max_retries=0` means behavior is identical unless a user opts in.

## Acceptance criteria

- [ ] respx test: 429 with `Retry-After: 1` then 200 → succeeds, exactly 2 requests, waited
      ≥1s (patch/measure sleep).
- [ ] respx test: retries exhausted → the original `RateLimitError` is raised with
      `retry_after` populated.
- [ ] respx test: non-idempotent POST is **not** retried by default.
- [ ] Default construction performs zero retries (single request on failure).
- [ ] README documents `RetryConfig` with an example.
