"""
Tests for the main SDK client: CodesphereSDK and APIHttpClient.
"""

import pytest
import httpx
from dataclasses import dataclass
from typing import Any, Optional, Type
from unittest.mock import AsyncMock, patch

from pydantic import BaseModel


# -----------------------------------------------------------------------------
# Test Models
# -----------------------------------------------------------------------------


class DummyModel(BaseModel):
    """A simple Pydantic model for testing."""

    name: str
    value: int


# -----------------------------------------------------------------------------
# Test Cases
# -----------------------------------------------------------------------------


@dataclass
class RequestTestCase:
    """Test case for HTTP request methods."""

    name: str
    method: str
    use_context_manager: bool
    payload: Any = None
    mock_status_code: int = 200
    expected_exception: Optional[Type[Exception]] = None


request_test_cases = [
    RequestTestCase(
        name="GET request successful",
        method="get",
        use_context_manager=True,
    ),
    RequestTestCase(
        name="POST request with Pydantic model successful",
        method="post",
        use_context_manager=True,
        payload=DummyModel(name="test", value=123),
    ),
    RequestTestCase(
        name="PUT request with dictionary successful",
        method="put",
        use_context_manager=True,
        payload={"key": "value"},
    ),
    RequestTestCase(
        name="Request fails without context manager",
        method="get",
        use_context_manager=False,
        expected_exception=RuntimeError,
    ),
    RequestTestCase(
        name="Request with 404 error raises HTTPStatusError",
        method="get",
        use_context_manager=True,
        mock_status_code=404,
        expected_exception=httpx.HTTPStatusError,
    ),
    RequestTestCase(
        name="Request with 500 error raises HTTPStatusError",
        method="post",
        use_context_manager=True,
        mock_status_code=500,
        expected_exception=httpx.HTTPStatusError,
    ),
]


# -----------------------------------------------------------------------------
# APIHttpClient Tests
# -----------------------------------------------------------------------------


class TestAPIHttpClient:
    """Tests for the APIHttpClient class."""

    def test_client_initialization(self, api_http_client, mock_token):
        """Client should initialize with token from settings."""
        assert api_http_client._token == mock_token

    def test_client_not_connected_initially(self, api_http_client):
        """Client should not be connected before entering context."""
        assert api_http_client._client is None

    @pytest.mark.asyncio
    async def test_client_connects_on_enter(self, api_http_client, mock_async_client):
        """Client should connect when entering context manager."""
        with patch("httpx.AsyncClient", return_value=mock_async_client):
            async with api_http_client as client:
                assert client._client is not None

    @pytest.mark.asyncio
    async def test_client_disconnects_on_exit(self, api_http_client, mock_async_client):
        """Client should disconnect when exiting context manager."""
        with patch("httpx.AsyncClient", return_value=mock_async_client):
            async with api_http_client:
                pass
            assert api_http_client._client is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "case", request_test_cases, ids=[c.name for c in request_test_cases]
    )
    async def test_client_requests(
        self,
        case: RequestTestCase,
        api_http_client,
        mock_response_factory,
    ):
        """Test various HTTP request scenarios."""
        mock_response = mock_response_factory.create(
            status_code=case.mock_status_code,
            json_data={},
        )
        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        mock_http_client.request.return_value = mock_response

        if case.expected_exception:
            with pytest.raises(case.expected_exception):
                with patch("httpx.AsyncClient", return_value=mock_http_client):
                    if case.use_context_manager:
                        async with api_http_client:
                            await getattr(api_http_client, case.method)(
                                "/test-endpoint"
                            )
                    else:
                        await getattr(api_http_client, case.method)("/test-endpoint")
            return

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            async with api_http_client:
                request_func = getattr(api_http_client, case.method)
                response = await request_func("/test-endpoint", json=case.payload)

                mock_http_client.request.assert_awaited_once()
                call_args = mock_http_client.request.call_args
                assert call_args.args[0] == case.method.upper()
                assert call_args.args[1] == "/test-endpoint"

                if isinstance(case.payload, BaseModel):
                    assert call_args.kwargs["json"] == case.payload.model_dump(
                        exclude_none=True
                    )
                else:
                    assert call_args.kwargs["json"] == case.payload

                assert response.status_code == case.mock_status_code


# -----------------------------------------------------------------------------
# CodesphereSDK Tests
# -----------------------------------------------------------------------------


class TestCodesphereSDK:
    """Tests for the CodesphereSDK class."""

    def test_sdk_has_teams_resource(self, sdk_client):
        """SDK should have teams resource attribute."""
        from codesphere.resources.team import TeamsResource

        assert hasattr(sdk_client, "teams")
        assert isinstance(sdk_client.teams, TeamsResource)

    def test_sdk_has_workspaces_resource(self, sdk_client):
        """SDK should have workspaces resource attribute."""
        from codesphere.resources.workspace import WorkspacesResource

        assert hasattr(sdk_client, "workspaces")
        assert isinstance(sdk_client.workspaces, WorkspacesResource)

    def test_sdk_has_metadata_resource(self, sdk_client):
        """SDK should have metadata resource attribute."""
        from codesphere.resources.metadata import MetadataResource

        assert hasattr(sdk_client, "metadata")
        assert isinstance(sdk_client.metadata, MetadataResource)

    @pytest.mark.asyncio
    async def test_sdk_context_manager(self, sdk_client, mock_async_client):
        """SDK should work as async context manager."""
        with patch("httpx.AsyncClient", return_value=mock_async_client):
            async with sdk_client as sdk:
                assert sdk is sdk_client
                # HTTP client should be connected
                assert sdk._http_client._client is not None

    @pytest.mark.asyncio
    async def test_sdk_open_and_close(self, sdk_client, mock_async_client):
        """SDK should support explicit open() and close() methods."""
        with patch("httpx.AsyncClient", return_value=mock_async_client):
            await sdk_client.open()
            assert sdk_client._http_client._client is not None

            await sdk_client.close()
            assert sdk_client._http_client._client is None
