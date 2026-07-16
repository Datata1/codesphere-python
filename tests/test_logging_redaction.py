"""Debug/error logs must never contain request/response payload values.

Env-var values and tokens are secrets; only structural information
(endpoint, param names, error locations) may be logged.
"""

import logging

import pytest
from pydantic import ValidationError

SECRET = "s3cret-value-do-not-log"
TOKEN = "test-token"


@pytest.fixture
def debug_caplog(caplog):
    caplog.set_level(logging.DEBUG, logger="codesphere")
    return caplog


class TestRequestLogging:
    async def test_request_body_values_are_not_logged(
        self, sdk, mock_api, debug_caplog
    ):
        mock_api.put("/workspaces/1/env-vars").respond(204)
        workspace = await _workspace(sdk, mock_api)

        await workspace.env_vars.set([{"name": "API_KEY", "value": SECRET}])

        assert SECRET not in debug_caplog.text
        assert TOKEN not in debug_caplog.text

    async def test_validation_error_does_not_log_response_body(
        self, sdk, mock_api, debug_caplog
    ):
        # Break the schema so validation fails while the body holds a secret.
        mock_api.get("/workspaces/2").respond(
            200, json={"id": "not-an-int", "secretField": SECRET}
        )

        with pytest.raises(ValidationError):
            await sdk.workspaces.get(2)

        assert SECRET not in debug_caplog.text


async def _workspace(sdk, mock_api, workspace_id: int = 1):
    mock_api.get(f"/workspaces/{workspace_id}").respond(
        200,
        json={
            "id": workspace_id,
            "teamId": 1,
            "name": "ws",
            "planId": 8,
            "isPrivateRepo": True,
            "replicas": 1,
            "dataCenterId": 1,
            "userId": 1,
            "restricted": False,
        },
    )
    return await sdk.workspaces.get(workspace_id)
