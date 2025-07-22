import asyncio
import pprint
from codesphere import CodesphereSDK


async def main():
    """Fetches datacenters."""
    async with CodesphereSDK() as sdk:
        datacenters = await sdk.metadata.datacenters()

        for datacenter in datacenters:
            pprint.pprint(datacenter.name)
            pprint.pprint(datacenter.city)
            pprint.pprint(datacenter.countryCode)
            pprint.pprint(datacenter.id)

if __name__ == "__main__":
    asyncio.run(main())
