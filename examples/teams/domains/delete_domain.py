import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        team = await sdk.teams.get(team_id=35663)
        domain = await team.domains.delete(domain_name="test.com")

        print(f"Domain created: {domain.name}")
        print(domain.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
