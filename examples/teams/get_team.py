import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    try:
        async with CodesphereSDK() as sdk:
            team = await sdk.teams.get(team_id="<id>")
            print(team.model_dump_json(indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
