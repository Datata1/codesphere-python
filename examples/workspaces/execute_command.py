import asyncio
import logging
from codesphere import CodesphereSDK

logging.basicConfig(level=logging.INFO)


async def main():
    async with CodesphereSDK() as sdk:
        teams = await sdk.teams.list()
        workspaces = await sdk.workspaces.list_by_team(team_id=teams[0].id)
        workspace = workspaces[0]
        state = await workspace.get_status()
        print(state.model_dump_json(indent=2))

        command_str = "echo Hello from $USER_NAME!"
        command_env = {"USER_NAME": "SDK-User"}

        command_output = await workspace.execute_command(
            command=command_str, env=command_env
        )
        print(command_output.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
