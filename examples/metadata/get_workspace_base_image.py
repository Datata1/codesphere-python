import asyncio
import pprint
from codesphere import CodesphereSDK


async def main():
    """Fetches base images."""
    async with CodesphereSDK() as sdk:
        images = await sdk.metadata.images()

        for image in images:
            pprint.pprint(image.id)
            pprint.pprint(image.name)
            pprint.pprint(image.supportedUntil)

if __name__ == "__main__":
    asyncio.run(main())
