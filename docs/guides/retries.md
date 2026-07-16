# Retries & timeouts

## Retries

Transient failures are retried automatically (2 retries by default).
Requests using an idempotent method (`GET`, `HEAD`, `PUT`, `DELETE`) are
retried on `429`, `502`, `503`, and `504` responses as well as on
connect/timeout errors. The delay honors the server's `Retry-After` header
(seconds or HTTP-date) when present, otherwise exponential backoff with
jitter (`backoff_factor * 2**attempt`).

Tune or disable the behavior with a `RetryConfig`:

```python
from codesphere import CodesphereSDK, RetryConfig

sdk = CodesphereSDK(
    token="your-api-token",
    retry=RetryConfig(max_retries=0),  # disable retries entirely
)
```

`POST` is never retried unless you add it to `retry_methods` explicitly
(only do this if your endpoints tolerate duplicate submissions):

```python
RetryConfig(max_retries=3, retry_methods=frozenset({"GET", "POST"}))
```

## Timeouts

Client-wide timeouts come from the constructor or environment
(see [Configuration](configuration.md)). Every API method additionally
accepts a keyword-only `timeout=` to override them for a single call —
a float (seconds, applied to connect and read) or a full `httpx.Timeout`:

```python
import httpx

# quick status probe: don't wait longer than 3 seconds
status = await workspace.get_status(timeout=3.0)

# long-running command: allow a slow read
result = await workspace.execute_command(
    "./run-migrations.sh",
    timeout=httpx.Timeout(10.0, read=600.0),
)
```

With retries enabled, a per-call timeout applies to each attempt
individually.

!!! note
    `workspace.wait_until_running(timeout=...)` and
    `workspace.logs.stream(timeout=...)` are *deadlines* for polling and
    streaming, not HTTP timeouts — they keep their own semantics.
