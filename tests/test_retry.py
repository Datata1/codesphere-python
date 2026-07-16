"""Retry behavior (on by default since max_retries=2), tested against respx."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from pydantic import SecretStr

from codesphere import APIError, CodesphereSDK, RateLimitError, RetryConfig
from codesphere.exceptions import TimeoutError
from codesphere.http_client import APIHttpClient, _parse_retry_after

BASE = "https://retry.test/api"


def make_transport(retry: RetryConfig | None = None) -> APIHttpClient:
    return APIHttpClient(
        token=SecretStr("t"),
        base_url=BASE,
        timeout=httpx.Timeout(5.0),
        retry=retry,
    )


@pytest.fixture
def api():
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def sleep_mock():
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock:
        yield mock


class TestRetryOnStatus:
    async def test_429_then_success_honors_retry_after(self, api, sleep_mock):
        route = api.get("/x")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(200, json={"ok": True}),
        ]
        async with make_transport(RetryConfig(max_retries=2)) as transport:
            response = await transport.request("GET", "/x")

        assert response.status_code == 200
        assert route.call_count == 2
        assert sleep_mock.await_count == 1
        assert sleep_mock.await_args.args[0] >= 1.0

    async def test_exhausted_retries_raise_rate_limit_with_retry_after(
        self, api, sleep_mock
    ):
        route = api.get("/x").respond(429, headers={"Retry-After": "7"}, json={})
        async with make_transport(RetryConfig(max_retries=2)) as transport:
            with pytest.raises(RateLimitError) as exc_info:
                await transport.request("GET", "/x")

        assert exc_info.value.retry_after == 7
        assert route.call_count == 3  # initial + 2 retries
        assert sleep_mock.await_count == 2

    async def test_backoff_grows_exponentially_without_header(self, api, sleep_mock):
        route = api.get("/x").respond(503, json={})
        config = RetryConfig(max_retries=2, backoff_factor=0.5)
        async with make_transport(config) as transport:
            with pytest.raises(APIError):
                await transport.request("GET", "/x")

        assert route.call_count == 3
        delays = [call.args[0] for call in sleep_mock.await_args_list]
        assert 0.5 <= delays[0] < 0.75  # 0.5 * 2**0 (+ jitter < 0.25)
        assert 1.0 <= delays[1] < 1.25  # 0.5 * 2**1 (+ jitter)

    async def test_non_retryable_status_fails_immediately(self, api, sleep_mock):
        route = api.get("/x").respond(500, json={})
        async with make_transport(RetryConfig(max_retries=3)) as transport:
            with pytest.raises(APIError):
                await transport.request("GET", "/x")

        assert route.call_count == 1  # 500 not in default retry_statuses
        sleep_mock.assert_not_awaited()


class TestRetryMethodGating:
    async def test_post_is_not_retried_by_default(self, api, sleep_mock):
        route = api.post("/x")
        route.side_effect = [httpx.Response(502), httpx.Response(200)]
        async with make_transport(RetryConfig(max_retries=3)) as transport:
            with pytest.raises(APIError):
                await transport.request("POST", "/x")

        assert route.call_count == 1
        sleep_mock.assert_not_awaited()

    async def test_post_can_be_opted_in(self, api, sleep_mock):
        route = api.post("/x")
        route.side_effect = [httpx.Response(502), httpx.Response(200)]
        config = RetryConfig(
            max_retries=3,
            retry_methods=frozenset({"GET", "HEAD", "PUT", "DELETE", "POST"}),
        )
        async with make_transport(config) as transport:
            response = await transport.request("POST", "/x")

        assert response.status_code == 200
        assert route.call_count == 2


class TestRetryOnTransportErrors:
    async def test_connect_timeout_is_retried(self, api, sleep_mock):
        route = api.get("/x")
        route.side_effect = [
            httpx.ConnectTimeout("slow"),
            httpx.Response(200, json={}),
        ]
        async with make_transport(RetryConfig(max_retries=1)) as transport:
            response = await transport.request("GET", "/x")

        assert response.status_code == 200
        assert route.call_count == 2

    async def test_exhausted_timeouts_raise_sdk_timeout(self, api, sleep_mock):
        api.get("/x").mock(side_effect=httpx.ConnectTimeout("slow"))
        async with make_transport(RetryConfig(max_retries=1)) as transport:
            with pytest.raises(TimeoutError):
                await transport.request("GET", "/x")

        assert sleep_mock.await_count == 1


class TestDefaults:
    async def test_default_config_retries_twice(self, api, sleep_mock):
        route = api.get("/x").respond(503, json={})
        async with make_transport() as transport:  # no RetryConfig
            with pytest.raises(APIError):
                await transport.request("GET", "/x")

        assert route.call_count == 3  # initial + 2 retries by default
        assert sleep_mock.await_count == 2

    async def test_default_config_recovers_from_transient_error(self, api, sleep_mock):
        route = api.get("/x")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(200, json={"ok": True}),
        ]
        async with make_transport() as transport:  # no RetryConfig
            response = await transport.request("GET", "/x")

        assert response.status_code == 200
        assert route.call_count == 2

    async def test_retries_can_be_disabled(self, api, sleep_mock):
        route = api.get("/x").respond(503, json={})
        async with make_transport(RetryConfig(max_retries=0)) as transport:
            with pytest.raises(APIError):
                await transport.request("GET", "/x")

        assert route.call_count == 1
        sleep_mock.assert_not_awaited()

    async def test_sdk_wires_retry_through(self, api, sleep_mock):
        route = api.get("/teams")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(200, json=[]),
        ]
        sdk = CodesphereSDK(token="t", base_url=BASE, retry=RetryConfig(max_retries=1))
        async with sdk:
            teams = await sdk.teams.list()

        assert teams == []
        assert route.call_count == 2
        assert sleep_mock.await_args.args[0] >= 2.0


class TestParseRetryAfter:
    def test_delta_seconds(self):
        assert _parse_retry_after("12") == 12.0

    def test_http_date_in_the_future(self):
        from datetime import UTC, datetime, timedelta
        from email.utils import format_datetime

        future = datetime.now(UTC) + timedelta(seconds=30)
        delay = _parse_retry_after(format_datetime(future, usegmt=True))
        assert delay is not None
        assert 28.0 < delay <= 30.0

    def test_http_date_in_the_past_clamps_to_zero(self):
        assert _parse_retry_after("Mon, 01 Jan 2001 00:00:00 GMT") == 0.0

    @pytest.mark.parametrize("value", [None, "", "soon", "-5"])
    def test_unparseable_values_return_none(self, value):
        assert _parse_retry_after(value) is None
