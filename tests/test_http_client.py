"""Direct unit tests for the APIHttpClient transport (respx-backed)."""

import httpx
import pytest
import respx
from pydantic import SecretStr

from codesphere.exceptions import NetworkError, TimeoutError
from codesphere.http_client import APIHttpClient

BASE = "https://transport.test/api"


@pytest.fixture
def transport():
    return APIHttpClient(
        token=SecretStr("secret"),
        base_url=BASE,
        timeout=httpx.Timeout(7.0, read=21.0),
    )


@pytest.fixture
def api():
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


class TestLifecycle:
    async def test_request_before_open_raises(self, transport):
        with pytest.raises(RuntimeError, match="not open"):
            await transport.request("GET", "/x")

    async def test_open_is_idempotent(self, transport, api):
        await transport.open()
        first = transport._client
        await transport.open()
        assert transport._client is first
        await transport.close()
        assert transport._client is None

    async def test_close_without_open_is_noop(self, transport):
        await transport.close()


class TestErrorMapping:
    @pytest.mark.parametrize(
        ("side_effect", "expected"),
        [
            (httpx.ConnectTimeout("t"), TimeoutError),
            (httpx.ReadTimeout("t"), TimeoutError),
            (httpx.PoolTimeout("t"), TimeoutError),
            (httpx.ConnectError("refused"), NetworkError),
            (httpx.ReadError("broken"), NetworkError),
            (httpx.RemoteProtocolError("bad"), NetworkError),
        ],
    )
    async def test_httpx_errors_map_to_sdk_errors(
        self, transport, api, side_effect, expected
    ):
        api.get("/x").mock(side_effect=side_effect)
        async with transport:
            with pytest.raises(expected):
                await transport.request("GET", "/x")


class TestConfigurationSurface:
    def test_timeout_property(self, transport):
        assert transport.timeout.read == 21.0

    def test_stream_timeout_keeps_connect_unbounds_read(self, transport):
        stream_timeout = transport.stream_timeout
        assert stream_timeout.connect == 7.0
        assert stream_timeout.read is None

    async def test_stream_passthrough(self, transport, api):
        api.get("/logs").respond(200, text="data: hi\n\n")
        async with transport, transport.stream("GET", "/logs") as response:
            body = await response.aread()
        assert b"data: hi" in body

    async def test_auth_header_configured(self, transport, api):
        route = api.get("/x").respond(200, json={})
        async with transport:
            await transport.request("GET", "/x")
        assert route.calls.last.request.headers["authorization"] == "Bearer secret"
