import asyncio
import pprint
from codesphere import CodesphereSDK, WorkspaceUpdate


async def main():
    """Fetches a workspace and updates its name."""
    workspace_id_to_update = 12245

    async with CodesphereSDK() as sdk:
        print(f"--- Fetching workspace with ID: {workspace_id_to_update} ---")
        workspace = await sdk.workspaces.get(workspace_id=workspace_id_to_update)

        print("Original workspace details:")
        pprint.pprint(workspace.model_dump())

        update_data = WorkspaceUpdate(name="updated workspace", planId=8)

        print(f"\n--- Updating workspace name to '{update_data.name}' ---")

        await workspace.update(data=update_data)

        print("\n--- Workspace successfully updated. New details: ---")
        pprint.pprint(workspace.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
