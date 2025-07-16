import asyncio
import os
import pprint
from codesphere import CodesphereClient


async def main(team_id: int, api_token: str = ""):
    api_token = api_token or os.getenv("CS_TOKEN")

    async with CodesphereClient(api_token) as client:
        status = await client.teams.teams_delete_team(team_id=team_id)

    pprint.pprint(status)


if __name__ == "__main__":
    asyncio.run(main("insert here teamid ro delete"))
