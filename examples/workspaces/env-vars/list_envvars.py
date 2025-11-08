import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    """Fetches a team and lists all workspaces within it."""
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        workspaces = await sdk.workspaces.list_by_team(team_id=teams[0].id)
        workspace = workspaces[0]

        envs = await workspace.env_vars.get()
        print("Current Environment Variables:")
        for env in envs:
            print(env.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
