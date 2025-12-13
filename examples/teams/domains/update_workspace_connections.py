import asyncio
import logging
from codesphere import CodesphereSDK, DomainRouting

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        team = await sdk.teams.get(team_id=35663)
        domainBuilder = DomainRouting()

        routing = (
            domainBuilder.add_route("/", [74861])
            .add_route("/api", [74868])
            .add_route("/test", [74868])
        )

        domain = await team.domains.update_workspace_connections(
            domain_name="test.com", connections=routing
        )
        print(f"Current routing: {domain.workspaces}")


if __name__ == "__main__":
    asyncio.run(main())
