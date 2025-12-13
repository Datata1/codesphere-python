import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        team = await sdk.teams.get(team_id=35663)
        domains = await team.domains.list()

        for domain in domains:
            print(f"Domain: {domain.name}")
            print(domain.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
