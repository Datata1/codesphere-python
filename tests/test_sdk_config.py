"""Configuration resolution tests for CodesphereSDK (refactor ticket 03)."""

import subprocess
import sys

import httpx
import pytest

from codesphere import AuthenticationError, CodesphereSDK


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """No CS_* env vars and no .env file in cwd."""
    for var in (
        "CS_TOKEN",
        "CS_BASE_URL",
        "CS_CLIENT_TIMEOUT_CONNECT",
        "CS_CLIENT_TIMEOUT_READ",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.chdir(tmp_path)
    return monkeypatch


def make_transport(seen: list) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    return httpx.MockTransport(handler)


async def fire_request(sdk: CodesphereSDK, seen: list) -> httpx.Request:
    """Issue one real request through the SDK against a mock transport."""
    sdk._http_client._client_config["transport"] = make_transport(seen)
    async with sdk:
        await sdk.teams.list()
    return seen[-1]


class TestImportWithoutEnvironment:
    def test_import_succeeds_without_any_env(self):
        """`import codesphere` must not require CS_TOKEN (ran in a subprocess
        with an empty environment so no .env or exported vars leak in)."""
        result = subprocess.run(
            [sys.executable, "-c", "import codesphere"],
            capture_output=True,
            text=True,
            env={},
            cwd="/tmp",
        )
        assert result.returncode == 0, result.stderr


class TestTokenResolution:
    def test_missing_token_raises_authentication_error(self, clean_env):
        with pytest.raises(AuthenticationError, match="CS_TOKEN"):
            CodesphereSDK()

    def test_explicit_token_argument(self, clean_env):
        sdk = CodesphereSDK(token="arg-token")
        assert sdk._http_client._token == "arg-token"

    def test_token_from_environment(self, clean_env):
        clean_env.setenv("CS_TOKEN", "env-token")
        sdk = CodesphereSDK()
        assert sdk._http_client._token == "env-token"

    def test_argument_wins_over_environment(self, clean_env):
        clean_env.setenv("CS_TOKEN", "env-token")
        sdk = CodesphereSDK(token="arg-token")
        assert sdk._http_client._token == "arg-token"

    async def test_two_clients_send_different_auth_headers(self, clean_env):
        seen_a: list = []
        seen_b: list = []
        request_a = await fire_request(CodesphereSDK(token="token-a"), seen_a)
        request_b = await fire_request(CodesphereSDK(token="token-b"), seen_b)

        assert request_a.headers["authorization"] == "Bearer token-a"
        assert request_b.headers["authorization"] == "Bearer token-b"


class TestBaseUrlResolution:
    async def test_explicit_base_url_argument(self, clean_env):
        seen: list = []
        sdk = CodesphereSDK(token="t", base_url="http://localhost:8000/api")
        request = await fire_request(sdk, seen)
        assert str(request.url) == "http://localhost:8000/api/teams"

    async def test_base_url_from_environment(self, clean_env):
        clean_env.setenv("CS_BASE_URL", "https://staging.example.com/api")
        seen: list = []
        request = await fire_request(CodesphereSDK(token="t"), seen)
        assert request.url.host == "staging.example.com"

    async def test_default_base_url(self, clean_env):
        seen: list = []
        request = await fire_request(CodesphereSDK(token="t"), seen)
        assert str(request.url) == "https://codesphere.com/api/teams"


class TestTimeoutResolution:
    def test_default_timeouts(self, clean_env):
        sdk = CodesphereSDK(token="t")
        timeout = sdk._http_client._timeout_config
        assert timeout.connect == 10.0
        assert timeout.read == 30.0

    def test_explicit_timeout_argument(self, clean_env):
        sdk = CodesphereSDK(token="t", timeout=httpx.Timeout(1.0, read=2.0))
        timeout = sdk._http_client._timeout_config
        assert timeout.connect == 1.0
        assert timeout.read == 2.0

    def test_timeouts_from_environment(self, clean_env):
        clean_env.setenv("CS_CLIENT_TIMEOUT_CONNECT", "3.5")
        clean_env.setenv("CS_CLIENT_TIMEOUT_READ", "7.5")
        sdk = CodesphereSDK(token="t")
        timeout = sdk._http_client._timeout_config
        assert timeout.connect == 3.5
        assert timeout.read == 7.5


class TestInjectedHttpClient:
    def test_injected_client_is_used_as_is(self, clean_env):
        from pydantic import SecretStr

        from codesphere.http_client import APIHttpClient

        transport = APIHttpClient(
            token=SecretStr("t"),
            base_url="https://example.com",
            timeout=httpx.Timeout(1.0),
        )
        sdk = CodesphereSDK(http_client=transport)
        assert sdk._http_client is transport
