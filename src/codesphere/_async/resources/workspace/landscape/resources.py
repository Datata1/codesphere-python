from __future__ import annotations

import asyncio
import base64
import logging
import re
from typing import TYPE_CHECKING

import httpx

from ....core.base import ResourceList, WorkspaceScopedResource
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


class WorkspaceLandscapeManager(WorkspaceScopedResource):
    async def _run_command(
        self, command: str, *, timeout: httpx.Timeout | float | None = None
    ) -> CommandOutput:
        from ..operations import _EXECUTE_COMMAND_OP
        from ..schemas import CommandInput

        return await self._execute(
            _EXECUTE_COMMAND_OP,
            id=self.workspace_id,
            data=CommandInput(command=command),
            timeout=timeout,
        )

    async def list_profiles(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> ResourceList[Profile]:
        result = await self._run_command(
            "ls -1 *.yml 2>/dev/null || true", timeout=timeout
        )

        profiles: list[Profile] = []
        if result.output:
            for line in result.output.strip().split("\n"):
                if match := _PROFILE_FILE_PATTERN.match(line.strip()):
                    profiles.append(Profile(name=match.group(1)))

        return ResourceList[Profile](root=profiles)

    async def save_profile(
        self,
        name: str,
        config: ProfileConfig | str,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        filename = _profile_filename(name)

        yaml_content = config.to_yaml() if isinstance(config, ProfileConfig) else config

        body = yaml_content if yaml_content.endswith("\n") else yaml_content + "\n"
        # Transport the content base64-encoded: the base64 alphabet is inert
        # inside single quotes, so arbitrary YAML cannot break out of the
        # shell command (the filename is regex-validated above).
        encoded = base64.b64encode(body.encode("utf-8")).decode("ascii")
        await self._run_command(
            f"printf '%s' '{encoded}' | base64 -d > '{filename}'", timeout=timeout
        )

    async def get_profile(
        self, name: str, *, timeout: httpx.Timeout | float | None = None
    ) -> str:
        result = await self._run_command(
            f"cat '{_profile_filename(name)}'", timeout=timeout
        )
        return result.output

    async def delete_profile(
        self, name: str, *, timeout: httpx.Timeout | float | None = None
    ) -> None:
        await self._run_command(f"rm -f '{_profile_filename(name)}'", timeout=timeout)

    async def deploy(
        self,
        profile: str | None = None,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        if profile is not None:
            _validate_profile_name(profile)
            await self._execute(
                _DEPLOY_WITH_PROFILE_OP,
                id=self.workspace_id,
                profile=profile,
                timeout=timeout,
            )
        else:
            await self._execute(_DEPLOY_OP, id=self.workspace_id, timeout=timeout)

    async def teardown(self, *, timeout: httpx.Timeout | float | None = None) -> None:
        await self._execute(_TEARDOWN_OP, id=self.workspace_id, timeout=timeout)

    async def scale(
        self,
        services: dict[str, int],
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        await self._execute(
            _SCALE_OP, id=self.workspace_id, data=services, timeout=timeout
        )

    async def start_stage(
        self,
        stage: PipelineStage | str,
        profile: str | None = None,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        if isinstance(stage, PipelineStage):
            stage = stage.value

        if profile is not None:
            _validate_profile_name(profile)
            await self._execute(
                _START_PIPELINE_STAGE_WITH_PROFILE_OP,
                id=self.workspace_id,
                stage=stage,
                profile=profile,
                timeout=timeout,
            )
        else:
            await self._execute(
                _START_PIPELINE_STAGE_OP,
                id=self.workspace_id,
                stage=stage,
                timeout=timeout,
            )

    async def stop_stage(
        self,
        stage: PipelineStage | str,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        if isinstance(stage, PipelineStage):
            stage = stage.value

        await self._execute(
            _STOP_PIPELINE_STAGE_OP, id=self.workspace_id, stage=stage, timeout=timeout
        )

    async def get_stage_status(
        self,
        stage: PipelineStage | str,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> PipelineStatusList:
        if isinstance(stage, PipelineStage):
            stage = stage.value

        return await self._execute(
            _GET_PIPELINE_STATUS_OP,
            id=self.workspace_id,
            stage=stage,
            timeout=timeout,
        )

    async def wait_for_stage(
        self,
        stage: PipelineStage | str,
        *,
        timeout: float = 300.0,
        poll_interval: float = 5.0,
        server: str | None = None,
    ) -> PipelineStatusList:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than 0")

        stage_name = stage.value if isinstance(stage, PipelineStage) else stage
        elapsed = 0.0

        while elapsed < timeout:
            status_list = await self.get_stage_status(stage)

            relevant_statuses = []
            for s in status_list:
                if server is not None:
                    if s.server == server:
                        relevant_statuses.append(s)
                else:
                    if s.steps or s.state != PipelineState.WAITING:
                        relevant_statuses.append(s)

            if not relevant_statuses:
                log.debug(
                    "Pipeline stage '%s': no servers with steps yet, waiting...",
                    stage_name,
                )
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                continue

            all_completed = all(
                s.state
                in (PipelineState.SUCCESS, PipelineState.FAILURE, PipelineState.ABORTED)
                for s in relevant_statuses
            )

            if all_completed:
                log.debug("Pipeline stage '%s' completed.", stage_name)
                return PipelineStatusList(root=relevant_statuses)

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
