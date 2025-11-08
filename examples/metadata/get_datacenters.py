import asyncio
from codesphere import CodesphereSDK


async def main():
    """Fetches datacenters."""
    async with CodesphereSDK() as sdk:
        datacenters = await sdk.metadata.datacenters()
        for datacenter in datacenters:
            print(datacenter.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
