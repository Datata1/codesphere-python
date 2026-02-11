"""
Codesphere Dashboard - A comprehensive example using FastAPI + HTMX.

This dashboard demonstrates all features of the Codesphere SDK:
- Teams: List, view details
- Workspaces: Create, list, update, delete, status monitoring
- Environment Variables: List, create, delete
- Commands: Execute shell commands on workspaces
- Pipeline/Landscape: Deploy profiles, start stages, monitor status
- Logs: View pipeline and server logs
- Git: View HEAD, pull changes
- Domains: List and manage custom domains
- Metadata: View plans, images, datacenters

Run with: uvicorn app:app --reload
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Load .env file from the dashboard directory
load_dotenv(Path(__file__).parent / ".env")

from codesphere import CodesphereSDK  # noqa: E402
from codesphere.resources.workspace import (  # noqa: E402
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
)
from codesphere.resources.workspace.envVars import EnvVar  # noqa: E402
from codesphere.resources.workspace.landscape import (  # noqa: E402
    PipelineStage,
    ProfileBuilder,
)
from codesphere.resources.workspace.logs import LogStage  # noqa: E402

# Global SDK instance (managed via lifespan)
cs: Optional[CodesphereSDK] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global cs
    cs = CodesphereSDK()
    await cs.open()
    yield
    await cs.close()


app = FastAPI(
    title="Codesphere Dashboard",
    description="A comprehensive example showcasing the Codesphere SDK",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# =============================================================================
# Template Filters
# =============================================================================


def format_datetime(value: Optional[datetime]) -> str:
    """Format datetime for display."""
    if value is None:
        return "N/A"
    return value.strftime("%Y-%m-%d %H:%M:%S")


templates.env.filters["datetime"] = format_datetime


# =============================================================================
# Helper Functions
# =============================================================================


def is_htmx_request(request: Request) -> bool:
    """Check if request is from HTMX."""
    return request.headers.get("HX-Request") == "true"


async def get_workspace_with_status(workspace: Workspace) -> dict:
    """Get workspace data with status."""
    try:
        status = await workspace.get_status()
        is_running = status.is_running
    except Exception:
        is_running = False

    return {
        "workspace": workspace,
        "is_running": is_running,
    }


# =============================================================================
# Home / Index Routes
# =============================================================================


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Dashboard home - show teams and infrastructure overview."""
    teams = await cs.teams.list()
    datacenters = await cs.metadata.list_datacenters()
    plans = await cs.metadata.list_plans()
    images = await cs.metadata.list_images()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "teams": teams,
            "datacenters": datacenters,
            "plans": [p for p in plans if not p.deprecated],
            "images": images,
        },
    )


# =============================================================================
# Team Routes
# =============================================================================


@app.get("/teams/{team_id}", response_class=HTMLResponse)
async def team_detail(request: Request, team_id: int):
    """Team detail page - show workspaces and domains."""
    team = await cs.teams.get(team_id=team_id)
    workspaces = await cs.workspaces.list(team_id=team_id)
    plans = await cs.metadata.list_plans()
    images = await cs.metadata.list_images()

    # Get status for all workspaces IN PARALLEL (much faster for large teams)
    workspace_data = await asyncio.gather(
        *[get_workspace_with_status(ws) for ws in workspaces]
    )

    # Get domains
    try:
        domains = await team.domains.list()
    except Exception:
        domains = []

    # Get usage summary (last 7 days)
    try:
        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=7)
        usage = await team.usage.get_landscape_summary(
            begin_date=begin_date, end_date=end_date, limit=10
        )
    except Exception:
        usage = None

    return templates.TemplateResponse(
        "team.html",
        {
            "request": request,
            "team": team,
            "workspaces": workspace_data,
            "domains": domains,
            "usage": usage,
            "plans": [p for p in plans if not p.deprecated],
            "images": images,
        },
    )


# =============================================================================
# Workspace Routes
# =============================================================================


@app.get("/workspaces/{workspace_id}", response_class=HTMLResponse)
async def workspace_detail(request: Request, workspace_id: int):
    """Workspace detail page with all management features."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)
    team = await cs.teams.get(team_id=workspace.team_id)
    plans = await cs.metadata.list_plans()

    # Get status
    try:
        status = await workspace.get_status()
        is_running = status.is_running
    except Exception:
        is_running = False

    # Get environment variables
    try:
        env_vars = await workspace.env_vars.list()
    except Exception:
        env_vars = []

    # Get git info
    try:
        git_head = await workspace.git.get_head()
    except Exception:
        git_head = None

    # Get pipeline status
    try:
        pipeline_status = await workspace.landscape.get_status()
    except Exception:
        pipeline_status = []

    # Get available profiles
    try:
        profiles = await workspace.landscape.list_profiles()
    except Exception:
        profiles = []

    return templates.TemplateResponse(
        "workspace.html",
        {
            "request": request,
            "workspace": workspace,
            "team": team,
            "is_running": is_running,
            "env_vars": env_vars,
            "git_head": git_head,
            "pipeline_status": pipeline_status,
            "profiles": profiles,
            "plans": plans,
        },
    )


@app.post("/workspaces/create", response_class=HTMLResponse)
async def create_workspace(
    request: Request,
    team_id: int = Form(...),
    name: str = Form(...),
    plan_id: int = Form(...),
    base_image: Optional[str] = Form(None),
    git_url: Optional[str] = Form(None),
):
    """Create a new workspace."""
    try:
        workspace = await cs.workspaces.create(
            WorkspaceCreate(
                team_id=team_id,
                name=name,
                plan_id=plan_id,
                base_image=base_image if base_image else None,
                git_url=git_url if git_url else None,
            )
        )
        return RedirectResponse(url=f"/workspaces/{workspace.id}", status_code=303)
    except Exception as e:
        # Return error partial for HTMX
        if is_htmx_request(request):
            return templates.TemplateResponse(
                "partials/error.html",
                {"request": request, "error": str(e)},
            )
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/workspaces/{workspace_id}/update", response_class=HTMLResponse)
async def update_workspace(
    request: Request,
    workspace_id: int,
    name: Optional[str] = Form(None),
    plan_id: Optional[int] = Form(None),
    replicas: Optional[int] = Form(None),
):
    """Update workspace settings."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)

    update_data = WorkspaceUpdate(
        name=name if name else None,
        plan_id=plan_id if plan_id else None,
        replicas=replicas if replicas else None,
    )
    await workspace.update(update_data)

    return RedirectResponse(url=f"/workspaces/{workspace_id}", status_code=303)


@app.post("/workspaces/{workspace_id}/delete")
async def delete_workspace(workspace_id: int):
    """Delete a workspace."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)
    team_id = workspace.team_id
    await workspace.delete()
    return RedirectResponse(url=f"/teams/{team_id}", status_code=303)


# =============================================================================
# Workspace Status (HTMX Polling)
# =============================================================================


@app.get("/partials/workspaces/{workspace_id}/status", response_class=HTMLResponse)
async def workspace_status_partial(request: Request, workspace_id: int):
    """Return workspace status badge (for HTMX polling)."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)
    try:
        status = await workspace.get_status()
        is_running = status.is_running
    except Exception:
        is_running = False

    return templates.TemplateResponse(
        "partials/workspace_status.html",
        {"request": request, "workspace": workspace, "is_running": is_running},
    )


# =============================================================================
# Environment Variables
# =============================================================================


@app.get("/partials/workspaces/{workspace_id}/env-vars", response_class=HTMLResponse)
async def env_vars_partial(request: Request, workspace_id: int):
    """Return environment variables list."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)
    try:
        env_vars = await workspace.env_vars.list()
    except Exception:
        env_vars = []

    return templates.TemplateResponse(
        "partials/env_vars.html",
        {"request": request, "workspace": workspace, "env_vars": env_vars},
    )


@app.post("/workspaces/{workspace_id}/env-vars", response_class=HTMLResponse)
async def add_env_var(
    request: Request,
    workspace_id: int,
    name: str = Form(...),
    value: str = Form(...),
):
    """Add an environment variable."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)
    await workspace.env_vars.set([EnvVar(name=name, value=value)])

    # Return updated list
    env_vars = await workspace.env_vars.list()
    return templates.TemplateResponse(
        "partials/env_vars.html",
        {"request": request, "workspace": workspace, "env_vars": env_vars},
    )


@app.delete(
    "/workspaces/{workspace_id}/env-vars/{var_name}", response_class=HTMLResponse
)
async def delete_env_var(request: Request, workspace_id: int, var_name: str):
    """Delete an environment variable."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)
    await workspace.env_vars.delete([var_name])

    # Return updated list
    env_vars = await workspace.env_vars.list()
    return templates.TemplateResponse(
        "partials/env_vars.html",
        {"request": request, "workspace": workspace, "env_vars": env_vars},
    )


# =============================================================================
# Command Execution
# =============================================================================


@app.post("/partials/workspaces/{workspace_id}/execute", response_class=HTMLResponse)
async def execute_command(
    request: Request,
    workspace_id: int,
    command: str = Form(...),
):
    """Execute a command on the workspace."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)

    try:
        result = await workspace.execute_command(command)
        output = result.output if result.output else result.error
        error = result.error if result.output else None
    except Exception as e:
        output = ""
        error = str(e)

    return templates.TemplateResponse(
        "partials/command_output.html",
        {
            "request": request,
            "command": command,
            "output": output,
            "error": error,
        },
    )


# =============================================================================
# Git Operations
# =============================================================================


@app.post("/workspaces/{workspace_id}/git/pull", response_class=HTMLResponse)
async def git_pull(request: Request, workspace_id: int):
    """Pull latest changes from git."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)

    try:
        await workspace.git.pull()
        git_head = await workspace.git.get_head()
        message = "Pull successful!"
        error = None
    except Exception as e:
        git_head = None
        message = None
        error = str(e)

    return templates.TemplateResponse(
        "partials/git_info.html",
        {
            "request": request,
            "workspace": workspace,
            "git_head": git_head,
            "message": message,
            "error": error,
        },
    )


# =============================================================================
# Pipeline / Landscape
# =============================================================================


@app.get("/partials/workspaces/{workspace_id}/pipeline", response_class=HTMLResponse)
async def pipeline_status_partial(request: Request, workspace_id: int):
    """Return pipeline status (for HTMX polling)."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)

    try:
        pipeline_status = await workspace.landscape.get_status()
    except Exception:
        pipeline_status = []

    try:
        profiles = await workspace.landscape.list_profiles()
    except Exception:
        profiles = []

    return templates.TemplateResponse(
        "partials/pipeline_status.html",
        {
            "request": request,
            "workspace": workspace,
            "pipeline_status": pipeline_status,
            "profiles": profiles,
        },
    )


@app.post("/workspaces/{workspace_id}/pipeline/deploy", response_class=HTMLResponse)
async def deploy_pipeline(
    request: Request,
    workspace_id: int,
    profile_name: str = Form(default="production"),
):
    """Deploy a landscape profile (creates a simple default profile)."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)
    plans = await cs.metadata.list_plans()
    plan = next((p for p in plans if not p.deprecated), plans[0])

    # Create a simple profile
    profile = (
        ProfileBuilder()
        .prepare()
        .add_step("echo 'Preparing workspace...'")
        .done()
        .test()
        .add_step("echo 'Running tests...'")
        .done()
        .add_reactive_service("app")
        .plan(plan.id)
        .add_step("echo 'Starting application...'")
        .add_port(3000, public=True)
        .replicas(1)
        .done()
        .build()
    )

    try:
        await workspace.landscape.save_profile(profile_name, profile)
        await workspace.landscape.deploy(profile=profile_name)
        message = f"Profile '{profile_name}' deployed successfully!"
        error = None
    except Exception as e:
        message = None
        error = str(e)

    # Return updated pipeline status
    try:
        pipeline_status = await workspace.landscape.get_status()
    except Exception:
        pipeline_status = []

    try:
        profiles = await workspace.landscape.list_profiles()
    except Exception:
        profiles = []

    return templates.TemplateResponse(
        "partials/pipeline_status.html",
        {
            "request": request,
            "workspace": workspace,
            "pipeline_status": pipeline_status,
            "profiles": profiles,
            "message": message,
            "error": error,
        },
    )


@app.post(
    "/workspaces/{workspace_id}/pipeline/start/{stage}", response_class=HTMLResponse
)
async def start_pipeline_stage(
    request: Request,
    workspace_id: int,
    stage: str,
    profile: str = Form(default="production"),
):
    """Start a pipeline stage."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)

    stage_map = {
        "prepare": PipelineStage.PREPARE,
        "test": PipelineStage.TEST,
        "run": PipelineStage.RUN,
    }

    if stage not in stage_map:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    try:
        await workspace.landscape.start_stage(stage_map[stage], profile=profile)
        message = f"Stage '{stage}' started!"
        error = None
    except Exception as e:
        message = None
        error = str(e)

    # Return updated status
    try:
        pipeline_status = await workspace.landscape.get_status()
    except Exception:
        pipeline_status = []

    try:
        profiles = await workspace.landscape.list_profiles()
    except Exception:
        profiles = []

    return templates.TemplateResponse(
        "partials/pipeline_status.html",
        {
            "request": request,
            "workspace": workspace,
            "pipeline_status": pipeline_status,
            "profiles": profiles,
            "message": message,
            "error": error,
        },
    )


# =============================================================================
# Logs
# =============================================================================


@app.get(
    "/partials/workspaces/{workspace_id}/logs-controls", response_class=HTMLResponse
)
async def logs_controls_partial(
    request: Request,
    workspace_id: int,
    stage: str = Query(default="prepare"),
):
    """Return logs control form with server list for run stage."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)

    # Get available servers from pipeline status (for run stage)
    servers = []
    if stage == "run":
        try:
            pipeline_status = await workspace.landscape.get_status()
            # Extract unique server names
            servers = list(
                {status.server for status in pipeline_status if status.server}
            )
        except Exception:
            pass

    return templates.TemplateResponse(
        "partials/logs_controls.html",
        {
            "request": request,
            "workspace": workspace,
            "stage": stage,
            "servers": servers,
        },
    )


@app.get("/partials/workspaces/{workspace_id}/logs", response_class=HTMLResponse)
async def logs_partial(
    request: Request,
    workspace_id: int,
    stage: str = Query(default="prepare"),
    step: int = Query(default=0),
    server: Optional[str] = Query(default=None),
    replica: Optional[int] = Query(default=None),
):
    """Get logs for a pipeline stage or server."""
    workspace = await cs.workspaces.get(workspace_id=workspace_id)

    stage_map = {
        "prepare": LogStage.PREPARE,
        "test": LogStage.TEST,
        "run": LogStage.RUN,
    }

    logs = []
    error = None

    try:
        if stage in stage_map:
            # Build kwargs for the collect call
            kwargs = {
                "stage": stage_map[stage],
                "step": step,
                "timeout": 5.0,
            }

            # Add server and replica for run stage
            if stage == "run" and server:
                kwargs["server"] = server
                if replica is not None:
                    kwargs["replica"] = replica

            log_entries = await workspace.logs.collect(**kwargs)
            logs = [entry.get_text() for entry in log_entries if entry.get_text()]
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse(
        "partials/logs.html",
        {
            "request": request,
            "workspace": workspace,
            "logs": logs,
            "stage": stage,
            "step": step,
            "server": server,
            "replica": replica,
            "error": error,
        },
    )


# =============================================================================
# Workspace List Partial (for HTMX refresh)
# =============================================================================


@app.get("/partials/teams/{team_id}/workspaces", response_class=HTMLResponse)
async def workspace_list_partial(request: Request, team_id: int):
    """Return workspace list for a team."""
    workspaces = await cs.workspaces.list(team_id=team_id)

    # Fetch all workspace statuses in parallel
    workspace_data = await asyncio.gather(
        *[get_workspace_with_status(ws) for ws in workspaces]
    )

    return templates.TemplateResponse(
        "partials/workspace_list.html",
        {"request": request, "workspaces": workspace_data, "team_id": team_id},
    )


# =============================================================================
# Run the app
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
