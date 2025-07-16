import asyncio
import pprint
from codesphere import CodesphereSDK


async def main():
    """Fetches a team and lists all workspaces within it."""
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        workspaces = await sdk.workspaces.list_by_team(team_id=teams[0].id)

        for workspace in workspaces:
            pprint.pprint(workspace.model_dump())
        print(f"Found {len(workspaces)} workspace(s):")
        for ws in workspaces:
            print(f"  - ID: {ws.id}, Name: {ws.name}, Status: {await ws.get_status()}")


if __name__ == "__main__":
    asyncio.run(main())
