"""
Codesphere SDK Demo - Marimo Notebook

This notebook demonstrates the capabilities of the Codesphere SDK with executable cells.
Run with: marimo run sdk_demo.py
Edit with: marimo edit sdk_demo.py
"""

import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium")

with app.setup:
    """Import dependencies and initialize the SDK."""
    import os
    from codesphere import CodesphereSDK

    # Display token status
    token = os.environ.get("CS_TOKEN")
    print(f"Token available: {bool(token)}")
    if token:
        print(f"Token prefix: {token[:8]}...")


@app.cell
def introduction():
    import marimo as mo

    mo.md(
        """
        # 🚀 Codesphere SDK Interactive Demo

        This notebook contains **executable code cells** to explore the SDK.
        Make sure you have `CS_TOKEN` set in your environment.
        """
    )
    return (mo,)


@app.cell
async def list_teams():
    """List all teams you have access to."""
    if not token:
        print("⚠️ No CS_TOKEN set - skipping")
    else:
        async with CodesphereSDK() as sdk:
            teams = await sdk.teams.list()
            print(f"Found {len(teams)} team(s):\n")
            for team in teams:
                print(f"  • {team.name} (ID: {team.id})")
    return


@app.cell
def select_team(mo):
    """Input for selecting a team to work with."""
    team_id_input = mo.ui.number(
        value=0,
        start=0,
        label="Enter Team ID to explore:",
    )
    team_id_input
    return (team_id_input,)


@app.cell
async def list_workspaces(team_id_input):
    """List workspaces for the selected team."""
    team_id = int(team_id_input.value)

    if not token:
        print("⚠️ No CS_TOKEN set - skipping")
    elif team_id <= 0:
        print("👆 Enter a Team ID above to list workspaces")
    else:
        async with CodesphereSDK() as sdk:
            workspaces = await sdk.workspaces.list(team_id=team_id)
            print(f"Found {len(workspaces)} workspace(s) in team {team_id}:\n")
            for ws in workspaces:
                print(f"  • {ws.name}")
                print(f"      ID: {ws.id}")
                print(f"      Plan: {ws.plan}")
                print(f"      Status: {ws.status}")
                print()
    return


@app.cell
def select_workspace(mo):
    """Input for selecting a workspace to inspect."""
    workspace_id_input = mo.ui.number(
        value=0,
        start=0,
        label="Enter Workspace ID to inspect:",
    )
    workspace_id_input
    return (workspace_id_input,)


@app.cell
async def get_workspace_details(workspace_id_input):
    """Get detailed information about a specific workspace."""
    workspace_id = int(workspace_id_input.value)

    if not token:
        print("⚠️ No CS_TOKEN set - skipping")
    elif workspace_id <= 0:
        print("👆 Enter a Workspace ID above to get details")
    else:
        async with CodesphereSDK() as sdk:
            workspace = await sdk.workspaces.get(workspace_id=workspace_id)
            print("Workspace Details:")
            print(f"{'─' * 40}")
            print(f"Name:       {workspace.name}")
            print(f"ID:         {workspace.id}")
            print(f"Plan:       {workspace.plan}")
            print(f"Status:     {workspace.status}")
            print(f"Team ID:    {workspace.team_id}")
            print(f"{'─' * 40}")
    return


@app.cell
def workspace_table_section(mo):
    mo.md("""
    ## 📊 Workspaces Table View
    """)
    return


@app.cell
async def workspaces_table(mo, team_id_input):
    """Display workspaces as an interactive table."""
    team_id = int(team_id_input.value)

    if not token:
        mo.output.replace(mo.md("⚠️ No CS_TOKEN set"))
    elif team_id <= 0:
        mo.output.replace(mo.md("*Enter a Team ID above*"))
    else:
        async with CodesphereSDK() as sdk:
            workspaces = await sdk.workspaces.list(team_id=team_id)
            if workspaces:
                data = [
                    {
                        "ID": ws.id,
                        "Name": ws.name,
                        "Plan": ws.plan,
                        "Status": ws.status,
                    }
                    for ws in workspaces
                ]
                mo.output.replace(mo.ui.table(data))
            else:
                mo.output.replace(mo.md("*No workspaces found*"))
    return


@app.cell
def pipeline_section(mo):
    mo.md("""
    ## 🔄 Pipeline Operations

    Select a workspace and run pipeline stages:
    """)
    return


@app.cell
def pipeline_controls(mo):
    """Controls for running pipeline operations."""
    pipeline_workspace_id = mo.ui.number(
        value=0,
        start=0,
        label="Workspace ID:",
    )
    pipeline_stage = mo.ui.dropdown(
        options=["prepare", "test", "run"],
        value="prepare",
        label="Pipeline Stage:",
    )
    run_pipeline_btn = mo.ui.run_button(label="Run Pipeline")

    mo.hstack([pipeline_workspace_id, pipeline_stage, run_pipeline_btn])
    return pipeline_stage, pipeline_workspace_id, run_pipeline_btn


@app.cell
async def execute_pipeline(
    mo,
    pipeline_stage,
    pipeline_workspace_id,
    run_pipeline_btn,
):
    """Execute a pipeline stage on the selected workspace."""
    if not run_pipeline_btn.value:
        mo.output.replace(mo.md("*Click 'Run Pipeline' to execute*"))
    elif not token:
        mo.output.replace(mo.md("⚠️ No CS_TOKEN set"))
    elif int(pipeline_workspace_id.value) <= 0:
        mo.output.replace(mo.md("⚠️ Enter a valid Workspace ID"))
    else:
        ws_id = int(pipeline_workspace_id.value)
        stage = pipeline_stage.value

        try:
            async with CodesphereSDK() as sdk:
                workspace = await sdk.workspaces.get(workspace_id=ws_id)
                mo.output.replace(
                    mo.md(f"🔄 Running **{stage}** on {workspace.name}...")
                )

                if stage == "prepare":
                    await workspace.pipelines.run_prepare()
                elif stage == "test":
                    await workspace.pipelines.run_test()
                elif stage == "run":
                    await workspace.pipelines.run_run()

                mo.output.replace(mo.md(f"✅ **{stage}** completed successfully!"))
        except Exception as e:
            mo.output.replace(mo.md(f"❌ Error: {e}"))
    return


@app.cell
def raw_api_section(mo):
    mo.md("""
    ## 🔧 Raw SDK Objects

    Explore the raw SDK objects and their attributes:
    """)
    return


@app.cell
async def show_raw_workspace(workspace_id_input):
    """Show the raw workspace object data."""
    workspace_id = int(workspace_id_input.value)

    if not token:
        print("⚠️ No CS_TOKEN set")
    elif workspace_id <= 0:
        print("Enter a Workspace ID above")
    else:
        async with CodesphereSDK() as sdk:
            workspace = await sdk.workspaces.get(workspace_id=workspace_id)
            # Show the model as a dict
            print("Raw workspace data:")
            print(workspace.model_dump_json(indent=2))
    return


if __name__ == "__main__":
    app.run()
