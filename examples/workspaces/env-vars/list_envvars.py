import asyncio
import pprint
from codesphere import CodesphereSDK


async def main():
    """Fetches a team and lists all workspaces within it."""
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        workspaces = await sdk.workspaces.list_by_team(team_id=teams[0].id)

        workspace = workspaces[0]

        envs = await workspace.get_env_vars()
        print("Current Environment Variables:")
        pprint.pprint(envs)


if __name__ == "__main__":
    asyncio.run(main())
