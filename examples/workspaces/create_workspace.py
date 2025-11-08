import asyncio
import logging
from codesphere import CodesphereSDK, WorkspaceCreate

logging.basicConfig(level=logging.INFO)


async def main():
    team_id = int(999999)

    async with CodesphereSDK() as sdk:
        print(f"--- Creating a new workspace in team {team_id} ---")
        workspace_data = WorkspaceCreate(
            name="my-new-sdk-workspace-3",
            planId=8,
            teamId=team_id,
            isPrivateRepo=True,
            replicas=1,
        )

        created_workspace = await sdk.workspaces.create(data=workspace_data)
        print(created_workspace.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
