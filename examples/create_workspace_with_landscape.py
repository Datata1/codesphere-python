import asyncio
import time

from codesphere import CodesphereSDK
from codesphere.resources.workspace import WorkspaceCreate
from codesphere.resources.workspace.landscape import ProfileBuilder, ProfileConfig

TEAM_ID = 123  # Replace with your actual team ID


async def get_plan_id(sdk: CodesphereSDK, plan_name: str = "Micro") -> int:
    plans = await sdk.metadata.list_plans()
    plan = next((p for p in plans if p.title == plan_name and not p.deprecated), None)
    if not plan:
        raise ValueError(f"Plan '{plan_name}' not found")
    return plan.id


def build_web_profile(plan_id: int) -> ProfileConfig:
    """Build a simple web service landscape profile."""
    return (
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
        .build()
    )


async def create_workspace(sdk: CodesphereSDK, plan_id: int, name: str):
    workspace = await sdk.workspaces.create(
        WorkspaceCreate(plan_id=plan_id, team_id=TEAM_ID, name=name)
    )
    await workspace.wait_until_running(timeout=300.0, poll_interval=5.0)
    return workspace


async def deploy_landscape(workspace, profile: dict, profile_name: str = "production"):
    await workspace.landscape.save_profile(profile_name, profile)
    await workspace.landscape.deploy(profile=profile_name)
    print("Deployment started!")


async def main():
    async with CodesphereSDK() as sdk:
        plan_id = await get_plan_id(sdk)
        workspace = await create_workspace(
            sdk, plan_id, f"landscape-demo-{int(time.time())}"
        )
        profile = build_web_profile(plan_id)
        await deploy_landscape(workspace, profile)


if __name__ == "__main__":
    asyncio.run(main())
