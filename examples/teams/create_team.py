import asyncio
import pprint

from codesphere import CodesphereSDK


async def main():
    try:
        async with CodesphereSDK() as sdk:
            created_team = await sdk.teams.create(name="hello", dc=2)
            print("\n--- Details for the created team ---")
            pprint.pprint(created_team.model_dump())

            print(f"Team ID: {created_team.id}, Name: {created_team.name}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
