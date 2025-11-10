import asyncio
import logging
from codesphere import CodesphereSDK, CustomDomainConfig

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        domain = await sdk.domains.get(team_id=35663, domain_name="test.com")
        print(domain.model_dump_json(indent=2))
        newConfig = CustomDomainConfig(
            max_body_size_mb=24, max_connection_timeout_s=50, restricted=True
        )
        await domain.update_domain(data=newConfig)
        print(domain.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
