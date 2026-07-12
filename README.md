<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://codesphere.com/img/codesphere-light.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://codesphere.com/img/codesphere-dark.svg">
    <img src="https://static.codesphere.com/assets/img/logo.svg" alt="Codesphere" width="300">
  </picture>
</p>

<h1 align="center">Python SDK</h1>

<p align="center">
  <a href="https://pypi.org/project/codesphere/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/codesphere.svg?style=flat-square">
  </a>
  <a href="https://pypi.org/project/codesphere/">
    <img alt="Python" src="https://img.shields.io/pypi/pyversions/codesphere.svg?style=flat-square">
  </a>
  <a href="https://github.com/Datata1/codesphere-python/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/pypi/l/codesphere.svg?style=flat-square">
  </a>
</p>

<p align="center">
  <strong>The official Python client for the <a href="https://codesphere.com/api/swagger-ui/">Codesphere API</a>.</strong>
</p>



---

## Installation

```bash
uv add codesphere
```

## Configuration

Every option can be passed directly to the constructor:

```python
from codesphere import CodesphereSDK

sdk = CodesphereSDK(token="your-api-token")
# or, e.g. against a different deployment:
sdk = CodesphereSDK(token="your-api-token", base_url="https://my-instance.example.com/api")
```

Alternatively, configure via environment variables (or a `.env` file in your
project root). Explicit constructor arguments always win over the environment:

| Variable | Description | Default |
|----------|-------------|---------|
| `CS_TOKEN` | API token (required) | – |
| `CS_BASE_URL` | API base URL | `https://codesphere.com/api` |

If no token is provided at all, `CodesphereSDK()` raises an
`AuthenticationError` at construction (importing the package never requires
any environment variable).

### Retries

Retries are off by default. Opt in with a `RetryConfig`:

```python
from codesphere import CodesphereSDK, RetryConfig

sdk = CodesphereSDK(
    token="your-api-token",
    retry=RetryConfig(max_retries=3),
)
```

Requests using an idempotent method (`GET`, `HEAD`, `PUT`, `DELETE`) are then
retried on `429`, `502`, `503`, and `504` responses as well as on
connect/timeout errors. The delay honors the server's `Retry-After` header
(seconds or HTTP-date) when present, otherwise exponential backoff with
jitter (`backoff_factor * 2**attempt`). `POST` is never retried unless you
add it to `retry_methods` explicitly:

```python
RetryConfig(max_retries=3, retry_methods=frozenset({"GET", "POST"}))
```

### Feature flags

Platform instances enable different features. Inspect them via `sdk.flags`:

```python
snapshot = await sdk.flags.get()          # fetched once, then cached
if await sdk.flags.is_enabled("workspace-ssh"):
    ...

await sdk.flags.refresh()                 # re-fetch after platform changes
```

SDK features that depend on a platform flag raise `FeatureNotEnabledError`
(or `FeatureNotAvailableError` if the instance doesn't have the feature at
all) *before* sending any request when the flag is off.

## Quick Start

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

## Usage

### Teams

```python
teams = await sdk.teams.list()
team = await sdk.teams.get(team_id=123)
await team.delete()
```

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

## Development

```bash
git clone https://github.com/Datata1/codesphere-python.git
cd codesphere-python
uv sync --all-extras
uv run pytest
```

## License

MIT – see [LICENSE](LICENSE) for details.
