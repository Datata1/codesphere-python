"""Lifecycle tests for the generated sync client."""

import pytest

from codesphere import AuthenticationError, RetryConfig
from codesphere.sync import CodesphereSDK

BASE = "https://sync.test/api"


class TestLifecycle:
    def test_context_manager_opens_and_closes(self, mock_api, sample_team_json):
        mock_api.get("/teams").respond(200, json=[sample_team_json])
        with CodesphereSDK(token="t", base_url=BASE) as sdk:
            assert sdk.teams.list()[0].id == 1
        assert sdk._http_client._client is None

    def test_open_close_explicitly(self, mock_api, sample_team_json):
        mock_api.get("/teams").respond(200, json=[sample_team_json])
        sdk = CodesphereSDK(token="t", base_url=BASE)
        sdk.open()
        try:
            assert len(sdk.teams.list()) == 1
        finally:
            sdk.close()

    def test_request_before_open_raises(self):
        sdk = CodesphereSDK(token="t", base_url=BASE)
        with pytest.raises(RuntimeError, match="not open"):
            sdk.teams.list()

    def test_missing_token_raises_authentication_error(self, monkeypatch):
        monkeypatch.delenv("CS_TOKEN", raising=False)
        monkeypatch.setattr(
            "codesphere._sync.client.Settings",
            lambda: type("S", (), {"token": None})(),
        )
        with pytest.raises(AuthenticationError):
            CodesphereSDK()

    def test_retry_config_is_wired(self):
        sdk = CodesphereSDK(token="t", base_url=BASE, retry=RetryConfig(max_retries=5))
        assert sdk._http_client._retry.max_retries == 5
