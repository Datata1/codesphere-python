from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from ....core.base import ResourceList
from ....core.handler import _APIOperationExecutor
from ....http_client import APIHttpClient
from .operations import (
    _DEPLOY_OP,
    _DEPLOY_WITH_PROFILE_OP,
    _GET_PIPELINE_STATUS_OP,
    _SCALE_OP,
    _START_PIPELINE_STAGE_OP,
    _START_PIPELINE_STAGE_WITH_PROFILE_OP,
    _STOP_PIPELINE_STAGE_OP,
    _TEARDOWN_OP,
)
from .schemas import (
    PipelineStage,
    PipelineState,
    PipelineStatusList,
    Profile,
    ProfileConfig,
)

if TYPE_CHECKING:
    from ..schemas import CommandOutput

log = logging.getLogger(__name__)

# Regex pattern to match ci.<profile>.yml files
_PROFILE_FILE_PATTERN = re.compile(r"^ci\.([A-Za-z0-9_-]+)\.yml$")
# Pattern for valid profile names
_VALID_PROFILE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


def _validate_profile_name(name: str) -> None:
    if not _VALID_PROFILE_NAME.match(name):
        raise ValueError(
            f"Invalid profile name '{name}'. Must match pattern ^[A-Za-z0-9_-]+$"
        )


def _profile_filename(name: str) -> str:
    _validate_profile_name(name)
    return f"ci.{name}.yml"


class WorkspaceLandscapeManager(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id
        self.id = workspace_id

    async def _run_command(self, command: str) -> "CommandOutput":
        from ..operations import _EXECUTE_COMMAND_OP
        from ..schemas import CommandInput

        return await self._execute_operation(
            _EXECUTE_COMMAND_OP, data=CommandInput(command=command)
        )

    async def list_profiles(self) -> ResourceList[Profile]:
        result = await self._run_command("ls -1 *.yml 2>/dev/null || true")

        profiles: List[Profile] = []
        if result.output:
            for line in result.output.strip().split("\n"):
                if match := _PROFILE_FILE_PATTERN.match(line.strip()):
                    profiles.append(Profile(name=match.group(1)))

        return ResourceList[Profile](root=profiles)

    async def save_profile(self, name: str, config: Union[ProfileConfig, str]) -> None:
        filename = _profile_filename(name)

        if isinstance(config, ProfileConfig):
            yaml_content = config.to_yaml()
        else:
            yaml_content = config

        body = yaml_content if yaml_content.endswith("\n") else yaml_content + "\n"
        await self._run_command(
            f"cat > {filename} << 'PROFILE_EOF'\n{body}PROFILE_EOF\n"
        )

    async def get_profile(self, name: str) -> str:
        result = await self._run_command(f"cat {_profile_filename(name)}")
        return result.output

    async def delete_profile(self, name: str) -> None:
        await self._run_command(f"rm -f {_profile_filename(name)}")

    async def deploy(self, profile: Optional[str] = None) -> None:
        if profile is not None:
            _validate_profile_name(profile)
            await self._execute_operation(_DEPLOY_WITH_PROFILE_OP, profile=profile)
        else:
            await self._execute_operation(_DEPLOY_OP)

    async def teardown(self) -> None:
        await self._execute_operation(_TEARDOWN_OP)

    async def scale(self, services: Dict[str, int]) -> None:
        await self._execute_operation(_SCALE_OP, data=services)

    # Pipeline operations

    async def start_stage(
        self,
        stage: Union[PipelineStage, str],
        profile: Optional[str] = None,
    ) -> None:
        """Start a pipeline stage.

        Args:
            stage: The pipeline stage to start ('prepare', 'test', or 'run').
            profile: Optional profile name. If provided, starts the stage with
                     that profile. Required for first run after deploy.

        Raises:
            ValidationError: If the workspace is not running or parameters are invalid.
            NotFoundError: If the workspace is not found.
        """
        if isinstance(stage, PipelineStage):
            stage = stage.value

        if profile is not None:
            _validate_profile_name(profile)
            await self._execute_operation(
                _START_PIPELINE_STAGE_WITH_PROFILE_OP, stage=stage, profile=profile
            )
        else:
            await self._execute_operation(_START_PIPELINE_STAGE_OP, stage=stage)

    async def stop_stage(self, stage: Union[PipelineStage, str]) -> None:
        """Stop a pipeline stage.

        Args:
            stage: The pipeline stage to stop ('prepare', 'test', or 'run').

        Raises:
            ValidationError: If the workspace is not running or parameters are invalid.
            NotFoundError: If the workspace is not found.
        """
        if isinstance(stage, PipelineStage):
            stage = stage.value

        await self._execute_operation(_STOP_PIPELINE_STAGE_OP, stage=stage)

    async def get_stage_status(
        self, stage: Union[PipelineStage, str]
    ) -> PipelineStatusList:
        """Get the status of a pipeline stage.

        Args:
            stage: The pipeline stage to get status for ('prepare', 'test', or 'run').

        Returns:
            List of PipelineStatus objects, one per replica/server.

        Raises:
            ValidationError: If the workspace is not running or parameters are invalid.
            NotFoundError: If the workspace is not found.
        """
        if isinstance(stage, PipelineStage):
            stage = stage.value

        return await self._execute_operation(_GET_PIPELINE_STATUS_OP, stage=stage)

    async def wait_for_stage(
        self,
        stage: Union[PipelineStage, str],
        *,
        timeout: float = 300.0,
        poll_interval: float = 5.0,
        server: Optional[str] = None,
    ) -> PipelineStatusList:
        """Wait for a pipeline stage to complete (success or failure).

        Args:
            stage: The pipeline stage to wait for.
            timeout: Maximum time to wait in seconds (default: 300).
            poll_interval: Time between status checks in seconds (default: 5).
            server: Optional server name to filter by. If None, waits for all
                    servers that have steps defined for this stage.

        Returns:
            Final PipelineStatusList when stage completes.

        Raises:
            TimeoutError: If the stage doesn't complete within the timeout.
            ValidationError: If the workspace is not running.
        """
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than 0")

        stage_name = stage.value if isinstance(stage, PipelineStage) else stage
        elapsed = 0.0

        while elapsed < timeout:
            status_list = await self.get_stage_status(stage)

            # Filter to relevant servers for THIS stage
            # A server is relevant for this stage if:
            # - It has steps defined (meaning it participates in this stage)
            # - OR it's not in 'waiting' state (meaning it has started)
            relevant_statuses = []
            for s in status_list:
                if server is not None:
                    # Filter by specific server
                    if s.server == server:
                        relevant_statuses.append(s)
                else:
                    # Include servers that have steps for this stage
                    # Servers with no steps and waiting state don't participate in this stage
                    if s.steps:
                        relevant_statuses.append(s)
                    elif s.state != PipelineState.WAITING:
                        # Started but no steps visible yet
                        relevant_statuses.append(s)

            # If no relevant statuses yet, keep waiting
            if not relevant_statuses:
                log.debug(
                    "Pipeline stage '%s': no servers with steps yet, waiting...",
                    stage_name,
                )
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                continue

            # Check if all relevant servers have completed
            all_completed = all(
                s.state
                in (PipelineState.SUCCESS, PipelineState.FAILURE, PipelineState.ABORTED)
                for s in relevant_statuses
            )

            if all_completed:
                log.debug("Pipeline stage '%s' completed.", stage_name)
                return PipelineStatusList(root=relevant_statuses)

            # Log current state
            states = [f"{s.server}={s.state.value}" for s in relevant_statuses]
            log.debug(
                "Pipeline stage '%s' status: %s (elapsed: %.1fs)",
                stage_name,
                ", ".join(states),
                elapsed,
            )
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"Pipeline stage '{stage_name}' did not complete within {timeout} seconds."
        )
