"""
Demo: Create a workspace, deploy a landscape profile, and stream logs.
"""

import asyncio
import time

from codesphere import CodesphereSDK
from codesphere.resources.workspace import WorkspaceCreate
from codesphere.resources.workspace.landscape import (
    PipelineStage,
    PipelineState,
    ProfileBuilder,
)
from codesphere.resources.workspace.logs import LogStage

TEAM_ID = 35698


async def main():
    async with CodesphereSDK() as sdk:
        plans = await sdk.metadata.list_plans()
        plan = next((p for p in plans if p.title == "Micro" and not p.deprecated), None)
        if not plan:
            raise ValueError("Micro plan not found")

        workspace_name = f"pipeline-demo-{int(time.time())}"
        print(f"Creating workspace '{workspace_name}'...")

        workspace = await sdk.workspaces.create(
            WorkspaceCreate(plan_id=plan.id, team_id=TEAM_ID, name=workspace_name)
        )
        print(f"✓ Workspace created (ID: {workspace.id})")

        print("Waiting for workspace to start...")
        await workspace.wait_until_running(timeout=300.0, poll_interval=5.0)
        print("✓ Workspace is running\n")

        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("echo 'Installing dependencies...' && sleep 2")
            .add_step("echo 'Setup complete!' && sleep 1")
            .done()
            .add_reactive_service("web")
            .plan(plan.id)
            .add_step(
                'for i in $(seq 1 50); do echo "[$i] Processing request..."; sleep 1; done'
            )
            .add_port(3000, public=True)
            .add_path("/", port=3000)
            .replicas(1)
            .done()
            .build()
        )

        print("Deploying landscape profile...")
        await workspace.landscape.save_profile("production", profile)
        await workspace.landscape.deploy(profile="production")
        print("✓ Profile deployed\n")

        print("--- Prepare Stage ---")
        await workspace.landscape.start_stage(
            PipelineStage.PREPARE, profile="production"
        )
        prepare_status = await workspace.landscape.wait_for_stage(
            PipelineStage.PREPARE, timeout=60.0
        )

        for status in prepare_status:
            icon = "✓" if status.state == PipelineState.SUCCESS else "✗"
            print(f"{icon} {status.server}: {status.state.value}")

        print("\nPrepare logs:")
        for step in range(len(prepare_status[0].steps)):
            logs = await workspace.logs.collect(
                stage=LogStage.PREPARE, step=step, timeout=5.0
            )
            for entry in logs:
                if entry.get_text():
                    print(f"  {entry.get_text().strip()}")

        print("\n--- Run Stage ---")
        await workspace.landscape.start_stage(PipelineStage.RUN, profile="production")
        print("Started run stage, waiting for logs...\n")

        print("Streaming logs from 'web' service:")
        count = 0
        async for entry in workspace.logs.stream_server(step=0, server="web"):
            if entry.get_text():
                print(f"  {entry.get_text().strip()}")
                count += 1

        print(f"\n✓ Stream ended ({count} log entries)")
        print(f"✓ Workspace {workspace.id} is still running.")


if __name__ == "__main__":
    asyncio.run(main())
