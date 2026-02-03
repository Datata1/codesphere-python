import asyncio
import logging
from codesphere import CodesphereSDK, CustomDomainConfig

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        team = await sdk.teams.get(team_id=35663)
        domain = await team.domains.get(domain_name="test.com")

        new_config_data = CustomDomainConfig(
            max_body_size_mb=24, max_connection_timeout_s=500, use_regex=False
        )
        await domain.update(new_config_data)


if __name__ == "__main__":
    asyncio.run(main())
