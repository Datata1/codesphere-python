import asyncio
import time
from datetime import datetime, timedelta, timezone

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

        # Get the team for usage history access
        team = await sdk.teams.get(team_id=TEAM_ID)

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
                'for i in $(seq 1 20); do echo "[$i] Processing request..."; sleep 1; done'
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
        print("Started run stage\n")

        print("Streaming logs from 'web' service (using context manager):")
        count = 0
        async with workspace.logs.open_server_stream(step=0, server="web") as stream:
            async for entry in stream:
                if entry.get_text():
                    print(f"  {entry.get_text().strip()}")
                    count += 1

        print(f"\n✓ Stream ended ({count} log entries)")

        # ========================================
        # Usage History Collection
        # ========================================
        print("\n--- Usage History ---")

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=1)

        print(
            f"Fetching usage summary from {begin_date.isoformat()} to {end_date.isoformat()}..."
        )
        usage_summary = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
            limit=50,
        )

        print(f"Total resources with usage: {usage_summary.total_items}")
        print(f"Page {usage_summary.current_page} of {usage_summary.total_pages}")

        if usage_summary.items:
            print("\nResource Usage Summary:")
            for item in usage_summary.items:
                hours = item.usage_seconds / 3600
                print(f"  • {item.resource_name}")
                print(f"    - Plan: {item.plan_name}")
                print(
                    f"    - Usage: {hours:.2f} hours ({item.usage_seconds:.0f} seconds)"
                )
                print(f"    - Replicas: {item.replicas}")
                print(f"    - Always On: {item.always_on}")
                print()

            first_resource = usage_summary.items[0]
            print(f"Fetching events for '{first_resource.resource_name}'...")

            events = await team.usage.get_landscape_events(
                resource_id=first_resource.resource_id,
                begin_date=begin_date,
                end_date=end_date,
            )

            print(f"Total events: {events.total_items}")
            for event in events.items:
                print(
                    f"  [{event.date.isoformat()}] {event.action.value.upper()} by {event.initiator_email}"
                )

            print("\nRefreshing usage summary...")
            await usage_summary.refresh()
            print(f"✓ Refreshed - still {usage_summary.total_items} items")
        else:
            print("No usage data found for the specified time range.")

        print("\n--- Auto-Pagination Example ---")
        print("Iterating through ALL usage summaries (auto-pagination):")
        item_count = 0
        async for item in team.usage.iter_all_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
            page_size=25,  # Fetch 25 at a time
        ):
            item_count += 1
            print(f"  {item_count}. {item.resource_id}: {item.usage_seconds:.0f}s")

        print(f"\n✓ Total items processed: {item_count}")


if __name__ == "__main__":
    asyncio.run(main())
