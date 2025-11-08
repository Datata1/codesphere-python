import asyncio
from codesphere import CodesphereSDK


async def main():
    """Fetches workspace plans."""
    async with CodesphereSDK() as sdk:
        plans = await sdk.metadata.plans()

        for plan in plans:
            print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
