import asyncio
from codesphere import CodesphereSDK


async def main():
    """Fetches base images."""
    async with CodesphereSDK() as sdk:
        images = await sdk.metadata.images()
        for image in images:
            print(image.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
