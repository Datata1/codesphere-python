import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    """Fetches base images."""
    async with CodesphereSDK() as sdk:
        images = await sdk.metadata.list_images()
        for image in images:
            print(image.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
