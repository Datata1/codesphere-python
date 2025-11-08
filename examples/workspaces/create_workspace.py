import asyncio
import pprint
from codesphere import CodesphereSDK, WorkspaceCreate


async def main():
    """Creates a new workspace in a specific team."""
    team_id = 12345

    async with CodesphereSDK() as sdk:
        print(f"--- Creating a new workspace in team {team_id} ---")

        workspace_data = WorkspaceCreate(
            name="my-new-sdk-workspace-3",
            planId=8,
            teamId=int(team_id),
            isPrivateRepo=True,
            replicas=1,
        )

        created_workspace = await sdk.workspaces.create(data=workspace_data)

        print("\n--- Details of successfully created workspace ---")
        pprint.pprint(created_workspace.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
