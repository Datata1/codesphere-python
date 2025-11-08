import asyncio
import logging
from codesphere import CodesphereSDK

# --- Logging-Konfiguration ---
logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        all_teams = await sdk.teams.list()
        first_team = all_teams[0]
        team_id_to_fetch = first_team.id
        workspaces = await sdk.workspaces.list_by_team(team_id=team_id_to_fetch)
        print(f"\n--- Workspaces in Team: {first_team.name} ---")
        for ws in workspaces:
            print(ws.model_dump_json(indent=2))
            print("-" * 20)


if __name__ == "__main__":
    asyncio.run(main())
