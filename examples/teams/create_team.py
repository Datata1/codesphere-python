import asyncio
from codesphere import CodesphereSDK, TeamCreate


async def main():
    try:
        async with CodesphereSDK() as sdk:
            newTeam = TeamCreate(name="test", dc=2)
            created_team = await sdk.teams.create(data=newTeam)
            print("\n--- Details for the created team ---")
            print(created_team.model_dump_json(indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
