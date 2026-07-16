# Streaming logs

Workspace logs are delivered as Server-Sent Events. The `workspace.logs`
manager streams them as typed `LogEntry` objects.

## Targets

A log target selects what to stream:

- `StageTarget(stage, step)` — a pipeline stage (`prepare`, `test`, `run`)
- `ServerTarget(step, server)` — one server of a Multi Server Deployment
- `ReplicaTarget(step, server, replica)` — a single replica

## Stream entries as they arrive

```python
from codesphere.resources.workspace import LogStage
from codesphere.resources.workspace.logs import StageTarget

workspace = await sdk.workspaces.get(workspace_id=456)

async for entry in workspace.logs.stream(StageTarget(LogStage.RUN, step=1)):
    print(entry.message)
```

## Collect entries into a list

```python
entries = await workspace.logs.collect(
    StageTarget(LogStage.TEST, step=1),
    max_entries=200,
    timeout=30.0,
)
```

`timeout` here is a *stream deadline* in seconds — collection stops when it
elapses (or when `max_entries` is reached), it is not an HTTP timeout.

## Manual stream control

`open()` returns the stream as an async context manager for full control:

```python
async with workspace.logs.open(StageTarget(LogStage.RUN, step=1)) as stream:
    async for entry in stream:
        if "ready" in entry.message:
            break
```
