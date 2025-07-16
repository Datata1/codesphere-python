import asyncio
from codesphere import CodesphereSDK


async def main():
    """Deletes a specific workspace."""

    workspace_id_to_delete = 12345

    async with CodesphereSDK() as sdk:
        print(f"--- Fetching workspace with ID: {workspace_id_to_delete} ---")
        workspace_to_delete = await sdk.workspaces.get(
            workspace_id=workspace_id_to_delete
        )

        print(f"\n--- Deleting workspace: '{workspace_to_delete.name}' ---")

        # This is a destructive action!
        await workspace_to_delete.delete()

        print(f"Workspace '{workspace_to_delete.name}' has been successfully deleted.")


if __name__ == "__main__":
    asyncio.run(main())
