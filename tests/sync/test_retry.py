"""Retry behavior of the generated sync transport (time.sleep based)."""

from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from codesphere import APIError, RetryConfig
from codesphere._sync.http_client import APIHttpClient

BASE = "https://sync-retry.test/api"


def make_transport(retry: RetryConfig | None = None) -> APIHttpClient:
    return APIHttpClient(
        token=SecretStr("t"),
        base_url=BASE,
        timeout=httpx.Timeout(5.0),
        retry=retry,
    )


@pytest.fixture
def api():
    import respx

    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def sleep_mock():
    with patch("codesphere._sync.http_client.time.sleep") as mock:
        yield mock


class TestSyncRetry:
    def test_429_then_success_honors_retry_after(self, api, sleep_mock):
        route = api.get("/x")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(200, json={"ok": True}),
        ]
        with make_transport(RetryConfig(max_retries=2)) as transport:
            response = transport.request("GET", "/x")

        assert response.status_code == 200
        assert route.call_count == 2
        assert sleep_mock.call_count == 1
        assert sleep_mock.call_args.args[0] >= 1.0

    def test_default_config_retries_twice(self, api, sleep_mock):
        route = api.get("/x").respond(503, json={})
        with make_transport() as transport, pytest.raises(APIError):
            transport.request("GET", "/x")

        assert route.call_count == 3
        assert sleep_mock.call_count == 2

    def test_post_is_not_retried_by_default(self, api, sleep_mock):
        route = api.post("/x").respond(502, json={})
        with (
            make_transport(RetryConfig(max_retries=3)) as transport,
            pytest.raises(APIError),
        ):
            transport.request("POST", "/x")

        assert route.call_count == 1
        sleep_mock.assert_not_called()
