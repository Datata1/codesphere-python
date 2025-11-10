import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        domains = await sdk.domains.list(team_id=99999999)
        for domain in domains:
            print(domain.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
