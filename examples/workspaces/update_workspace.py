import asyncio
import logging
from codesphere import CodesphereSDK, WorkspaceUpdate

logging.basicConfig(level=logging.INFO)


async def main():
    """Fetches a workspace and updates its name."""
    workspace_id_to_update = 72678

    async with CodesphereSDK() as sdk:
        workspace = await sdk.workspaces.get(workspace_id=workspace_id_to_update)
        print(workspace.model_dump_json(indent=2))

        update_data = WorkspaceUpdate(name="updated workspace2", planId=8)
        await workspace.update(data=update_data)
        print(workspace.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
