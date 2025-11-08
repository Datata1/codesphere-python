import asyncio
import logging
from codesphere import CodesphereSDK, EnvVar

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        workspaces = await sdk.workspaces.list_by_team(team_id=teams[0].id)
        workspace = workspaces[0]

        new_vars = [
            EnvVar(name="MY_NEW_VAR", value="hello_world"),
            EnvVar(name="ANOTHER_VAR", value="123456"),
        ]

        await workspace.env_vars.set(new_vars)

        print("\n--- Verifying new list ---")
        current_vars = await workspace.env_vars.get()
        for env in current_vars:
            print(env.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
