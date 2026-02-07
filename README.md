<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://codesphere.com/img/codesphere-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://codesphere.com/img/codesphere-light.svg">
    <img src="https://codesphere.com/img/codesphere-light.svg" alt="Codesphere" width="300">
  </picture>
</p>

<h1 align="center">Codesphere Python SDK</h1>

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
  <strong>The official Python client for the [Codesphere API](https://codesphere.com/api/swagger-ui/).</strong>
</p>



---

## Installation

```bash
uv add codesphere
```

## Configuration

Create a `.env` file in your project root:

| Variable | Description | Default |
|----------|-------------|---------|
| `CS_TOKEN` | API token (required) | – |
| `CS_BASE_URL` | API base URL | `https://codesphere.com/api` |

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

# Execute commands
result = await workspace.execute_command("ls -la")
print(result.output)

# Manage environment variables
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
