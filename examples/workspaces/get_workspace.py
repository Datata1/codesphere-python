import asyncio
from codesphere import CodesphereSDK


async def main():
    """Fetches a workspace within a Team."""
    async with CodesphereSDK() as sdk:
        pass


if __name__ == "__main__":
    asyncio.run(main())
