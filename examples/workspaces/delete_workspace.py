import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    """Deletes a specific workspace."""

    workspace_id_to_delete = int(9999999)

    async with CodesphereSDK() as sdk:
        workspace_to_delete = await sdk.workspaces.get(
            workspace_id=workspace_id_to_delete
        )

        print(f"\n--- Deleting workspace: '{workspace_to_delete.name}' ---")
        await workspace_to_delete.delete()
        print(f"Workspace '{workspace_to_delete.name}' has been successfully deleted.")


if __name__ == "__main__":
    asyncio.run(main())
