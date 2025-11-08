import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    try:
        async with CodesphereSDK() as sdk:
            team_to_delete = await sdk.teams.get(team_id=11111)
            print(team_to_delete.model_dump_json(indent=2))
            await team_to_delete.delete()
            print(f"Team with ID {team_to_delete.id} was successfully deleted.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
