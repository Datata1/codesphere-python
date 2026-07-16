# Quickstart

## 1. Install

```bash
uv add codesphere
```

## 2. Provide a token

Create an API token in Codesphere, then export it (or put it in a `.env` file):

```bash
export CS_TOKEN="your-api-token"
```

## 3. Make your first call

```python
import asyncio

from codesphere import CodesphereSDK


async def main():
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        for team in teams:
            print(f"{team.name} (ID: {team.id})")


asyncio.run(main())
```

## Common operations

### Workspaces

```python
workspaces = await sdk.workspaces.list(team_id=123)
workspace = await sdk.workspaces.get(workspace_id=456)

result = await workspace.execute_command("ls -la")
print(result.output)

await workspace.env_vars.set([{"name": "API_KEY", "value": "secret"}])
env_vars = await workspace.env_vars.get()
```

### Domains

```python
team = await sdk.teams.get(team_id=123)
domains = await team.domains.list()
domain = await team.domains.create(name="api.example.com")
```

### Metadata

```python
datacenters = await sdk.metadata.list_datacenters()
plans = await sdk.metadata.list_plans()
images = await sdk.metadata.list_images()
```

### Error handling

```python
from codesphere import CodesphereSDK, NotFoundError, RateLimitError

async with CodesphereSDK() as sdk:
    try:
        workspace = await sdk.workspaces.get(workspace_id=999999)
    except NotFoundError:
        print("Workspace does not exist")
    except RateLimitError as e:
        print(f"Rate limited, retry after {e.retry_after}s")
```

Continue with the [Configuration guide](guides/configuration.md) or the
[API Reference](reference/client.md).
