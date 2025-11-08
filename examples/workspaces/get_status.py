import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        all_teams = await sdk.teams.list()
        first_team = all_teams[0]
        workspaces = await sdk.workspaces.list_by_team(team_id=first_team.id)
        first_workspace = workspaces[0]
        state = await first_workspace.get_status()
        print(state.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
