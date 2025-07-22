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
        pprint.pprint(envs[0].name)

        await workspace.delete_env_vars([envs[0].name])  # you can pass a list of strings to delete multiple env vars

        print("Environment Variables after deletion:")
        updated_envs = await workspace.get_env_vars()
        pprint.pprint(updated_envs)

if __name__ == "__main__":
    asyncio.run(main())
