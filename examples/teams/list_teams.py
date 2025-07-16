import asyncio
import os
import pprint
from codesphere import CodesphereClient, Team


async def main(api_token: str = ""):
    api_token = api_token or os.getenv("CS_TOKEN")

    async with CodesphereClient(api_token) as client:
        teams: list[Team] = await client.teams.teams_list_teams()
        for team in teams:
            pprint.pprint(team.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
