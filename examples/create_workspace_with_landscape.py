import asyncio

from codesphere import CodesphereSDK
from codesphere.resources.workspace import WorkspaceCreate
from codesphere.resources.workspace.landscape import ProfileBuilder

TEAM_ID = 123  # Replace with your actual team ID


async def main():
    async with CodesphereSDK() as sdk:
        plans = await sdk.metadata.list_plans()
        plan_id = next(
            (p for p in plans if p.title == "Micro" and not p.deprecated), None
        ).id

        payload = WorkspaceCreate(
            plan_id,
            team_id=TEAM_ID,
            name=f"my-unique-landscape-demo-{int(asyncio.time())}",
        )

        print("\nCreating workspace...")
        workspace = await sdk.workspaces.create(payload)
        print(f"Created workspace: {workspace.name} (ID: {workspace.id})")

        try:
            print("Waiting for workspace to be running...")
            await workspace.wait_until_running(timeout=300.0, poll_interval=5.0)
            print("Workspace is now running!")

            print("\nCreating landscape profile...")
            profile = (
                ProfileBuilder()
                .prepare()
                .add_step("npm install", name="Install dependencies")
                .done()
                .add_reactive_service("web")
                .plan(plan_id)
                .add_step("npm start")
                .add_port(3000, public=True)
                .add_path("/", port=3000)
                .replicas(1)
                .env("NODE_ENV", "production")
                .done()
                .build()
            )

            profile_name = "production"
            await workspace.landscape.save_profile(profile_name, profile)
            print(f"Saved profile: {profile_name}")

            profiles = await workspace.landscape.list_profiles()
            print(f"Available profiles: {[p.name for p in profiles]}")

            yaml_content = await workspace.landscape.get_profile(profile_name)
            print(f"\nGenerated profile YAML:\n{yaml_content}")

            print("\nDeploying landscape...")
            await workspace.landscape.deploy(profile=profile_name)
            print("Deployment started!")

        finally:
            # Cleanup: Delete the workspace
            # print("\nCleaning up...")
            # await workspace.delete()
            # print(f"Deleted workspace: {workspace.name}")
            pass


if __name__ == "__main__":
    asyncio.run(main())
