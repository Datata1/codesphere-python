# Codesphere Dashboard Example

A comprehensive web dashboard demonstrating all features of the Codesphere SDK using FastAPI + HTMX.

## Features

This dashboard showcases the following SDK capabilities:

| Feature | SDK Methods Used |
|---------|------------------|
| **Teams** | `sdk.teams.list()`, `sdk.teams.get()` |
| **Workspaces** | `sdk.workspaces.list()`, `sdk.workspaces.create()`, `workspace.update()`, `workspace.delete()`, `workspace.get_status()` |
| **Environment Variables** | `workspace.env_vars.list()`, `workspace.env_vars.set()`, `workspace.env_vars.delete()` |
| **Command Execution** | `workspace.execute_command()` |
| **Pipeline/Landscape** | `workspace.landscape.save_profile()`, `workspace.landscape.deploy()`, `workspace.landscape.start_stage()`, `workspace.landscape.get_status()` |
| **Logs** | `workspace.logs.collect()` |
| **Git** | `workspace.git.get_head()`, `workspace.git.pull()` |
| **Domains** | `team.domains.list()` |
| **Usage** | `team.usage.get_landscape_summary()` |
| **Metadata** | `sdk.metadata.list_datacenters()`, `sdk.metadata.list_plans()`, `sdk.metadata.list_images()` |

## Tech Stack

- **FastAPI** - Async Python web framework
- **HTMX** - Dynamic HTML updates without JavaScript (via CDN)
- **Tailwind CSS** - Utility-first CSS framework (via CDN)
- **Jinja2** - Templating engine

## Quick Start

```bash
# Navigate to the dashboard directory
cd examples/dashboard

# Create a virtual environment
uv venv .venv

# Install dependencies and the SDK
uv pip install -r requirements.txt -e ../../

# Copy the example .env file and add your token
cp .env.example .env
# Edit .env and set your CS_TOKEN

# Run the dashboard
source .venv/bin/activate
uvicorn app:app --reload
```

Then open your browser to: http://localhost:8000

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Codesphere API token:
   ```
   CS_TOKEN=your-api-token-here
   ```

The dashboard automatically loads the `.env` file on startup.

## Project Structure

```
dashboard/
├── app.py                  # Main FastAPI application
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment file
├── .gitignore             # Ignores .venv, .env, __pycache__
├── README.md              # This file
├── static/
│   └── style.css          # Custom styles
└── templates/
    ├── base.html          # Base layout template
    ├── index.html         # Dashboard home page
    ├── team.html          # Team detail page
    ├── workspace.html     # Workspace management page
    └── partials/          # HTMX partial templates
        ├── command_output.html
        ├── env_vars.html
        ├── error.html
        ├── git_info.html
        ├── logs.html
        ├── pipeline_status.html
        ├── workspace_list.html
        └── workspace_status.html
```

## Pages

### Dashboard Home
- View all teams with avatars and datacenter info
- Infrastructure overview (datacenters, plans, images)
- SDK feature summary

### Team Detail
- Create new workspaces with form
- List all workspaces with live status
- View custom domains
- Usage summary for the last 7 days

### Workspace Management
- Real-time status indicator (auto-refreshes every 10s)
- Git repository info with pull button
- Environment variables management (add/delete)
- Command executor with terminal-like output
- Pipeline deployment and stage controls
- Log viewer for pipeline stages
- Workspace settings update form

## HTMX Features

This example demonstrates several HTMX patterns:

- **Polling**: Workspace status auto-updates every 10 seconds
- **Form Submissions**: All forms submit via HTMX for seamless updates
- **Partial Updates**: Only relevant sections refresh, not the whole page
- **Delete Confirmations**: Using `hx-confirm` for destructive actions
- **Loading States**: Visual feedback during requests

## License

MIT License - See the repository root for details.
