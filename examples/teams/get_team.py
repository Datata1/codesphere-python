import asyncio
import os
import pprint
from codesphere import CodesphereClient, Team


async def main(team_id: int, api_token: str = ""):
    api_token = api_token or os.getenv("CS_TOKEN")

    async with CodesphereClient(api_token) as client:
        team: Team = await client.teams.teams_get_team(team_id=team_id)

    pprint.pprint(team.model_dump())


if __name__ == "__main__":
    asyncio.run(main(team_id="insert team id here"))
