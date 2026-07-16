# Sync vs Async

The SDK ships two clients with identical APIs:

| | Async | Sync |
|---|---|---|
| Import | `from codesphere import CodesphereSDK` | `from codesphere.sync import CodesphereSDK` |
| Lifecycle | `async with CodesphereSDK() as sdk:` | `with CodesphereSDK() as sdk:` |
| Calls | `await sdk.teams.list()` | `sdk.teams.list()` |
| Streaming | `async for entry in ...` | `for entry in ...` |

Everything else — method names, parameters, configuration, retries,
feature-flag gating, exceptions — is the same. The sync client is
generated from the async source, and CI enforces that both surfaces
stay identical.

## Which one should I use?

- **Async** when your application already runs an event loop (FastAPI,
  aiohttp, background workers) or makes many concurrent API calls.
- **Sync** for scripts, CLIs, notebooks, and tools where `asyncio.run`
  would be ceremony.

## Shared models

Request and response payload classes live in `codesphere.models` and are
shared: a `WorkspaceCreate` built anywhere works with either client.

```python
from codesphere.models import WorkspaceCreate

payload = WorkspaceCreate(team_id=1, name="demo", plan_id=8)
```

## Per-flavor entities

Entities with API methods — `Workspace`, `Team`, `Domain`, `LogStream` —
exist once per flavor (`workspace.delete()` is `async` in one, plain in
the other). Consequently `isinstance` checks do not match across flavors:
`codesphere.Workspace` and `codesphere.sync.Workspace` are different
classes.

## Sync streaming caveat

`workspace.logs.stream(..., timeout=...)` enforces its deadline between
entries and via the socket read timeout. A stream that trickles bytes
just below the read timeout can overrun the deadline by up to one
interval — the same best-effort behavior most sync SSE clients have.
