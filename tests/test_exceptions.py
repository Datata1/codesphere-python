"""Unit tests for the exception hierarchy and raise_for_status mapping.

The matrix uses real httpx.Response objects (no mocks); the end-to-end
cases drive errors through the actual transport via respx.
"""

import httpx
import pytest

from codesphere import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    CodesphereError,
    ConflictError,
    FeatureFlagError,
    FeatureNotAvailableError,
    FeatureNotEnabledError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from codesphere.exceptions import raise_for_status


def make_response(
    status_code: int,
    json_body=None,
    text: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    request = httpx.Request("GET", "https://test.local/api/things/1")
    if json_body is not None:
        return httpx.Response(
            status_code, json=json_body, request=request, headers=headers
        )
    return httpx.Response(
        status_code, text=text or "", request=request, headers=headers
    )


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (400, ValidationError),
            (401, AuthenticationError),
            (403, AuthorizationError),
            (404, NotFoundError),
            (409, ConflictError),
            (422, ValidationError),
            (429, RateLimitError),
            (418, APIError),
            (500, APIError),
            (502, APIError),
            (503, APIError),
        ],
    )
    def test_status_raises_expected_class(self, status, expected):
        with pytest.raises(expected) as exc_info:
            raise_for_status(make_response(status, json_body={"message": "boom"}))
        assert isinstance(exc_info.value, CodesphereError)
        assert exc_info.value.message == "boom"

    @pytest.mark.parametrize("status", [200, 201, 204])
    def test_success_statuses_do_not_raise(self, status):
        raise_for_status(make_response(status))


class TestErrorMessageExtraction:
    @pytest.mark.parametrize(
        "body",
        [
            {"message": "from message"},
            {"error": "from error"},
            {"detail": "from detail"},
        ],
        ids=["message", "error", "detail"],
    )
    def test_message_keys(self, body):
        with pytest.raises(NotFoundError) as exc_info:
            raise_for_status(make_response(404, json_body=body))
        assert exc_info.value.message == next(iter(body.values()))

    def test_errors_list_is_joined(self):
        with pytest.raises(NotFoundError) as exc_info:
            raise_for_status(make_response(404, json_body={"errors": ["a", "b"]}))
        assert exc_info.value.message == "a; b"

    def test_non_json_body_uses_text(self):
        with pytest.raises(APIError) as exc_info:
            raise_for_status(make_response(500, text="Bad Gateway HTML"))
        assert exc_info.value.message == "Bad Gateway HTML"

    def test_empty_body_falls_back_to_default_message(self):
        with pytest.raises(AuthorizationError) as exc_info:
            raise_for_status(make_response(403, text=""))
        assert "permission" in exc_info.value.message

    def test_validation_error_collects_errors_field(self):
        body = {"message": "invalid", "errors": [{"field": "name"}]}
        with pytest.raises(ValidationError) as exc_info:
            raise_for_status(make_response(422, json_body=body))
        assert exc_info.value.errors == [{"field": "name"}]


class TestRateLimit:
    def test_retry_after_header_is_parsed(self):
        response = make_response(
            429, json_body={"message": "slow down"}, headers={"Retry-After": "17"}
        )
        with pytest.raises(RateLimitError) as exc_info:
            raise_for_status(response)
        assert exc_info.value.retry_after == 17

    def test_non_numeric_retry_after_is_ignored(self):
        response = make_response(
            429, json_body={}, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}
        )
        with pytest.raises(RateLimitError) as exc_info:
            raise_for_status(response)
        assert exc_info.value.retry_after is None

    def test_default_message_mentions_retry_after(self):
        error = RateLimitError(retry_after=30)
        assert "30" in error.message


class TestAPIErrorDetails:
    def test_request_context_is_captured(self):
        with pytest.raises(APIError) as exc_info:
            raise_for_status(make_response(500, json_body={}))
        error = exc_info.value
        assert error.status_code == 500
        assert error.request_method == "GET"
        assert error.request_url == "https://test.local/api/things/1"

    def test_str_includes_status_and_request(self):
        error = APIError(
            message="failed",
            status_code=502,
            request_url="https://x/y",
            request_method="POST",
        )
        assert str(error) == "failed | Status: 502 | Request: POST https://x/y"


class TestDefaultConstructors:
    """Every exported exception must be constructible with defaults."""

    @pytest.mark.parametrize(
        ("cls", "fragment"),
        [
            (CodesphereError, "error occurred"),
            (AuthenticationError, "CS_TOKEN"),
            (AuthorizationError, "permission"),
            (NotFoundError, "not found"),
            (ValidationError, "invalid"),
            (ConflictError, "conflicts"),
            (RateLimitError, "Rate limit"),
            (APIError, "API request failed"),
            (NetworkError, "network error"),
            (TimeoutError, "timed out"),
            (FeatureFlagError, "Feature flag"),
            (FeatureNotAvailableError, "not available"),
            (FeatureNotEnabledError, "not enabled"),
        ],
    )
    def test_default_message(self, cls, fragment):
        error = cls()
        assert fragment in error.message
        assert isinstance(error, CodesphereError)

    def test_not_found_with_resource_name(self):
        assert "workspace" in NotFoundError(resource="workspace").message

    def test_network_error_keeps_original(self):
        original = ConnectionResetError("reset")
        assert NetworkError(original_error=original).original_error is original

    def test_timeout_is_a_network_error(self):
        assert issubclass(TimeoutError, NetworkError)

    def test_flag_errors_share_a_base_and_carry_metadata(self):
        assert issubclass(FeatureNotAvailableError, FeatureFlagError)
        assert issubclass(FeatureNotEnabledError, FeatureFlagError)

        error = FeatureNotEnabledError(flag="vpn", category="internal")
        assert error.flag == "vpn"
        assert error.category == "internal"
        assert "'vpn' (category 'internal')" in error.message

    def test_not_available_mentions_legacy_platform_when_flagged(self):
        error = FeatureNotAvailableError(flag="vpn", legacy_platform=True)
        assert "predate feature flags" in error.message


class TestEndToEndViaTransport:
    """Errors surface through the real client against a mocked transport."""

    async def test_404_raises_not_found(self, sdk, mock_api):
        mock_api.get("/teams/1").respond(404, json={"message": "no such team"})
        with pytest.raises(NotFoundError, match="no such team"):
            await sdk.teams.get(team_id=1)

    async def test_429_carries_retry_after(self, sdk, mock_api):
        mock_api.get("/teams").respond(429, headers={"Retry-After": "5"}, json={})
        with pytest.raises(RateLimitError) as exc_info:
            await sdk.teams.list()
        assert exc_info.value.retry_after == 5

    async def test_timeout_maps_to_sdk_timeout_error(self, sdk, mock_api):
        mock_api.get("/teams").mock(side_effect=httpx.ConnectTimeout("slow"))
        with pytest.raises(TimeoutError):
            await sdk.teams.list()

    async def test_connect_error_maps_to_network_error(self, sdk, mock_api):
        mock_api.get("/teams").mock(side_effect=httpx.ConnectError("refused"))
        with pytest.raises(NetworkError):
            await sdk.teams.list()
