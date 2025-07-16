import asyncio

from codesphere import CodesphereSDK


async def main():
    try:
        async with CodesphereSDK() as sdk:
            teams = await sdk.teams.list()
            print(f"Found {len(teams)} teams:")
            for team in teams:
                print(f"Team ID: {team.id}, Name: {team.name}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
