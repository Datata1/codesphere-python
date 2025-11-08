import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        workspaces = await sdk.workspaces.list_by_team(team_id=teams[0].id)

        workspace = workspaces[0]
        vars_to_delete = await workspace.env_vars.get()
        for env in vars_to_delete:
            print(env.model_dump_json(indent=2))

        await workspace.env_vars.delete(vars_to_delete)

        print("\n--- Verifying deletion ---")
        current_vars = await workspace.env_vars.get()
        for env in current_vars:
            print(env.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
