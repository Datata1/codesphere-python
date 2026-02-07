from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from ....core.base import ResourceList
from ....core.handler import _APIOperationExecutor
from ....http_client import APIHttpClient
from .operations import (
    _DEPLOY_OP,
    _DEPLOY_WITH_PROFILE_OP,
    _SCALE_OP,
    _TEARDOWN_OP,
)
from .schemas import Profile, ProfileConfig

if TYPE_CHECKING:
    from ..schemas import CommandOutput

log = logging.getLogger(__name__)

# Regex pattern to match ci.<profile>.yml files
_PROFILE_FILE_PATTERN = re.compile(r"^ci\.([A-Za-z0-9_-]+)\.yml$")
# Pattern for valid profile names
_VALID_PROFILE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class WorkspaceLandscapeManager(_APIOperationExecutor):
    """Manager for workspace landscape operations (Multi Server Deployments)."""

    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id
        self.id = workspace_id

    async def list_profiles(self) -> ResourceList[Profile]:
        """List all available deployment profiles in the workspace.

        Profiles are discovered by listing files matching the pattern ci.<profile>.yml
        in the workspace root directory.

        Returns:
            ResourceList of Profile objects.
        """
        from ..operations import _EXECUTE_COMMAND_OP
        from ..schemas import CommandInput

        command_data = CommandInput(command="ls -1 *.yml 2>/dev/null || true")
        result: CommandOutput = await self._execute_operation(
            _EXECUTE_COMMAND_OP, data=command_data
        )

        profiles: List[Profile] = []
        if result.output:
            for line in result.output.strip().split("\n"):
                line = line.strip()
                if match := _PROFILE_FILE_PATTERN.match(line):
                    profile_name = match.group(1)
                    profiles.append(Profile(name=profile_name))

        return ResourceList[Profile](root=profiles)

    async def save_profile(self, name: str, config: Union[ProfileConfig, str]) -> None:
        """Save a profile configuration to the workspace.

        Args:
            name: Profile name (must match pattern ^[A-Za-z0-9_-]+$).
            config: ProfileConfig instance or YAML string.

        Raises:
            ValueError: If the profile name is invalid.
        """
        from ..operations import _EXECUTE_COMMAND_OP
        from ..schemas import CommandInput

        if not _VALID_PROFILE_NAME.match(name):
            raise ValueError(
                f"Invalid profile name '{name}'. Must match pattern ^[A-Za-z0-9_-]+$"
            )

        # Convert ProfileConfig to YAML if needed
        if isinstance(config, ProfileConfig):
            yaml_content = config.to_yaml()
        else:
            yaml_content = config

        # Escape single quotes in YAML content for shell
        escaped_content = yaml_content.replace("'", "'\"'\"'")

        # Write the profile file
        filename = f"ci.{name}.yml"
        command = f"cat > {filename} << 'PROFILE_EOF'\n{yaml_content}PROFILE_EOF"

        command_data = CommandInput(command=command)
        await self._execute_operation(_EXECUTE_COMMAND_OP, data=command_data)

    async def get_profile(self, name: str) -> str:
        """Get the raw YAML content of a profile.

        Args:
            name: Profile name.

        Returns:
            YAML content of the profile as a string.

        Raises:
            ValueError: If the profile name is invalid.
        """
        from ..operations import _EXECUTE_COMMAND_OP
        from ..schemas import CommandInput

        if not _VALID_PROFILE_NAME.match(name):
            raise ValueError(
                f"Invalid profile name '{name}'. Must match pattern ^[A-Za-z0-9_-]+$"
            )

        filename = f"ci.{name}.yml"
        command_data = CommandInput(command=f"cat {filename}")
        result: CommandOutput = await self._execute_operation(
            _EXECUTE_COMMAND_OP, data=command_data
        )

        return result.output

    async def delete_profile(self, name: str) -> None:
        """Delete a profile from the workspace.

        Args:
            name: Profile name to delete.

        Raises:
            ValueError: If the profile name is invalid.
        """
        from ..operations import _EXECUTE_COMMAND_OP
        from ..schemas import CommandInput

        if not _VALID_PROFILE_NAME.match(name):
            raise ValueError(
                f"Invalid profile name '{name}'. Must match pattern ^[A-Za-z0-9_-]+$"
            )

        filename = f"ci.{name}.yml"
        command_data = CommandInput(command=f"rm -f {filename}")
        await self._execute_operation(_EXECUTE_COMMAND_OP, data=command_data)

    async def deploy(self, profile: Optional[str] = None) -> None:
        """Deploy the landscape.

        Args:
            profile: Optional deployment profile name (must match pattern ^[A-Za-z0-9-_]+$).
        """
        if profile is not None:
            await self._execute_operation(_DEPLOY_WITH_PROFILE_OP, profile=profile)
        else:
            await self._execute_operation(_DEPLOY_OP)

    async def teardown(self) -> None:
        """Teardown the landscape."""
        await self._execute_operation(_TEARDOWN_OP)

    async def scale(self, services: Dict[str, int]) -> None:
        """Scale landscape services.

        Args:
            services: A dictionary mapping service names to replica counts (minimum 1).
        """
        await self._execute_operation(_SCALE_OP, data=services)
