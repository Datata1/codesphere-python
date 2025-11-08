import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    """Fetches workspace plans."""
    async with CodesphereSDK() as sdk:
        plans = await sdk.metadata.list_plans()

        for plan in plans:
            print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
