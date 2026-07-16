# Codesphere Python SDK

The official Python client for the [Codesphere API](https://codesphere.com/api/swagger-ui/).

- **Fully typed** — pydantic v2 models everywhere, ships `py.typed`; your editor is the documentation.
- **Async-first** — built on `httpx`, with async context-manager lifecycle.
- **Resilient by default** — automatic retries with backoff and `Retry-After` support.
- **Structured errors** — a complete exception hierarchy instead of raw HTTP errors.
- **Feature-flag aware** — operations that need a platform flag fail fast before sending anything.

## Installation

```bash
uv add codesphere
# or: pip install codesphere
```

## First call in three lines

```python
async with CodesphereSDK() as sdk:          # token from CS_TOKEN env var
    teams = await sdk.teams.list()
```

Head to the [Quickstart](quickstart.md) for a runnable example, or browse the
[API Reference](reference/client.md).
