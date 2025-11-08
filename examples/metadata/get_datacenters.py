import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    """Fetches datacenters."""
    async with CodesphereSDK() as sdk:
        datacenters = await sdk.metadata.list_datacenters()
        for datacenter in datacenters:
            print(datacenter.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
