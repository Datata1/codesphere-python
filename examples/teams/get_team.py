import asyncio

from codesphere import CodesphereSDK


async def main():
    try:
        async with CodesphereSDK() as sdk:
            teams = await sdk.teams.list()
            print(teams[0].model_dump_json(indent=2))
            first_team = await sdk.teams.get(team_id=teams[0].id)
            print("\n--- Details for the first team ---")
            print(first_team.model_dump_json(indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
