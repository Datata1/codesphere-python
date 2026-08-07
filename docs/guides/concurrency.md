# Concurrency

The async client is built to be shared. This guide covers what the SDK
guarantees when several tasks use it at once, and — just as important —
what it cannot guarantee, because the Codesphere API offers no way to.

## Share one client

Create one `CodesphereSDK` and use it from as many tasks as you like.
Sharing is preferred: each instance owns a connection pool, so creating
one per task throws away connection reuse.

```python
import asyncio
from codesphere import CodesphereSDK

async def main():
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        # One client, many concurrent calls.
        workspaces = await asyncio.gather(
            *(sdk.workspaces.list(team.id) for team in teams)
        )
```

Scopes are reference counted, so nested and concurrent `async with`
blocks are safe — the transport closes when the last one exits, not the
first:

```python
async def worker(sdk):
    async with sdk:              # each worker holds its own scope
        await sdk.teams.list()

async with CodesphereSDK() as sdk:
    await asyncio.gather(worker(sdk), worker(sdk))
    await sdk.teams.list()       # still open
```

Using the client after it is fully closed raises
[`ClientStateError`][codesphere.ClientStateError], which is both a
`CodesphereError` and a `RuntimeError`.

The synchronous client offers the same guarantees across threads.

## Models go stale after a write

The platform applies writes in the order they arrive; your program sees
them in the order responses come back. Those orders can differ, so the
SDK cannot know an entity's state after a write it did not read back.
Rather than report a value the platform may not hold, a write
**invalidates** the instance:

```python
workspace = await sdk.workspaces.get(72678)

await workspace.update(WorkspaceUpdate(name="renamed"))

workspace.id      # fine: a write cannot change an entity's identity
workspace.name    # raises StaleModelError
```

Call `refresh()` to re-read the server's actual state:

```python
await workspace.refresh()
workspace.name    # server-authoritative
```

This applies to `Workspace.update()`, `Domain.update()`,
`Domain.update_workspace_connections()` and `Domain.verify_status()`.
`to_dict()`, `to_json()` and `to_yaml()` raise on a stale model too.
The `Domain` methods return the server's response — prefer that returned
object over re-reading the instance you called them on.

## What the SDK cannot protect you from

The workspace you are reading can be changed at the same moment by the
web IDE, a CI pipeline, a teammate, or another process of your own. The
Codesphere API has **no ETags, no `If-Match`, and no idempotency keys**,
so there is no way for the SDK to detect or reject a conflicting write.
These are real limitations, not oversights, and the SDK does not pretend
otherwise.

### Read-modify-write loses concurrent changes

Any read, edit, write cycle has a window in which someone else's change
is silently overwritten:

```python
# NOT safe against concurrent writers
current = await workspace.env_vars.get()
await workspace.env_vars.set([*current, EnvVar(name="NEW", value="1")])
```

`env_vars.set()` is a full replacement (`PUT`), so a variable added by
someone else between the two calls is erased. The same applies to
`landscape.get_profile()` → edit → `save_profile()`, which writes through
a shell redirect and is not an atomic file replacement.

If you must do this, narrow the window and verify afterwards by reading
back. There is no way to make it atomic.

### Retried writes can execute twice

`PUT` and `DELETE` are idempotent as HTTP methods but not always in
effect. If the platform receives a request and only the response is lost
(a gateway `503`, a dropped connection), the retry runs the operation
again — a landscape teardown can happen twice. Without idempotency keys
the SDK cannot deduplicate this.

The most common symptom is handled: a `404` on a **retried** `DELETE` is
treated as success, since the resource being gone is what you asked for.
A `404` on the first attempt still raises `NotFoundError`.

If duplicate execution is unacceptable, disable retries for those calls:

```python
sdk = CodesphereSDK(retry=RetryConfig(max_retries=0))
```

### Waiting on a pipeline someone else restarted

`wait_for_stage()` pins the run it is watching by its start time. If
someone redeploys mid-wait, it raises
[`ConflictError`][codesphere.ConflictError] instead of reporting the
outcome of a run you never started:

```python
try:
    await workspace.landscape.wait_for_stage("run", timeout=600)
except ConflictError:
    # Someone else redeployed. Decide whether to wait on the new run.
    ...
```

Timeouts on `wait_for_stage()` and `wait_until_running()` are wall clock:
time spent inside the status requests counts against your budget.

## Log streams are single-use

`logs.open()` returns a stream backed by one SSE response body, which can
only be read once. Opening or iterating the same stream twice raises
`ClientStateError`. Call `logs.open()` again for a second stream —
concurrent streams over one client are fine:

```python
async def tail(target):
    async for entry in workspace.logs.stream(target):
        print(entry.message)

await asyncio.gather(
    tail(ServerTarget(step=1, server="web")),
    tail(ServerTarget(step=1, server="api")),
)
```

## Feature flags

The flags snapshot is fetched once per client and cached. Concurrent
gated calls collapse into a single request, and `invalidate()` is honored
even against a fetch that is already in flight.
