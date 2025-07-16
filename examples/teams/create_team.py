import asyncio
import os
import pprint
from codesphere import CodesphereClient, Team
from codesphere.models import TeamsCreateTeamRequest


async def main(api_token: str = ""):
    api_token = api_token or os.getenv("CS_TOKEN")

    request_args = TeamsCreateTeamRequest(
        name="Test Team",
        dc=2,  # data center 2 => FRA
    )

    async with CodesphereClient(api_token) as client:
        team: Team = await client.teams.teams_create_team(request_args)

    pprint.pprint(team.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
