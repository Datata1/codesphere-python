import asyncio
import pprint

from codesphere import CodesphereSDK


async def main():
    try:
        async with CodesphereSDK() as sdk:
            teams = await sdk.teams.list()
            first_team = await sdk.teams.get(team_id=teams[0].id)
            print("\n--- Details for the first team ---")
            pprint.pprint(first_team.model_dump())

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
