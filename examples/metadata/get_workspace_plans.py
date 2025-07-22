import asyncio
import pprint
from codesphere import CodesphereSDK


async def main():
    """Fetches workspace plans."""
    async with CodesphereSDK() as sdk:
        plans = await sdk.metadata.plans()

        for plan in plans:
            pprint.pprint(plan.id)
            pprint.pprint(plan.title)
            pprint.pprint(plan.priceUsd)
            pprint.pprint(plan.deprecated)
            pprint.pprint(plan.characteristics.id)
            pprint.pprint(plan.characteristics.CPU)
            pprint.pprint(plan.characteristics.GPU)
            pprint.pprint(plan.characteristics.RAM)
            pprint.pprint(plan.characteristics.SSD)
            pprint.pprint(plan.characteristics.TempStorage)
            pprint.pprint(plan.characteristics.onDemand)
            pprint.pprint(plan.maxReplicas)     

if __name__ == "__main__":
    asyncio.run(main())
