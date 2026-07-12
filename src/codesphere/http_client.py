import asyncio
import logging
import random
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from types import TracebackType
from typing import Any, cast

import httpx
from pydantic import SecretStr

from .config import RetryConfig
from .exceptions import NetworkError, TimeoutError, raise_for_status
from .feature_flags import FlagsStore

log = logging.getLogger(__name__)


def _parse_retry_after(value: str | None) -> float | None:
    """Parse a Retry-After header: delta-seconds or an HTTP-date."""
    if not value:
        return None
    if value.isdigit():
        return float(value)
    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())


class APIHttpClient:
    """Thin async transport around httpx.

    Receives its full configuration from the caller (the SDK resolves
    arguments, environment variables, and defaults) and owns nothing but
    the connection lifecycle, error mapping, and opt-in retries.
    """

    def __init__(
        self,
        *,
        token: SecretStr,
        base_url: str,
        timeout: httpx.Timeout,
        retry: RetryConfig | None = None,
    ):
        self._token = token.get_secret_value()
        self._base_url = base_url
        self._client: httpx.AsyncClient | None = None
        self._retry = retry if retry is not None else RetryConfig()
        # Per-connection feature-flags cache; the transport never reads it
        # itself (see feature_flags.FlagsStore).
        self.flags_store = FlagsStore(self)

        self._timeout_config = timeout
        self._client_config: dict[str, Any] = {
            "base_url": self._base_url,
            "headers": {"Authorization": f"Bearer {self._token}"},
            "timeout": self._timeout_config,
        }

    def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError(
                "Client is not open. Please use 'async with sdk:' "
                "or call 'await sdk.open()' before making requests."
            )
        return self._client

    @property
    def timeout(self) -> httpx.Timeout:
        """The configured request timeouts."""
        return self._timeout_config

    @property
    def stream_timeout(self) -> httpx.Timeout:
        """Timeouts for long-lived streams: configured connect, unbounded read."""
        # httpx.Timeout attributes are untyped upstream; connect is float | None
        connect = cast("float | None", self._timeout_config.connect)
        return httpx.Timeout(connect, read=None)

    def stream(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> AbstractAsyncContextManager[httpx.Response]:
        """Open a streaming request (e.g. SSE) on the underlying client."""
        return self._get_client().stream(method, endpoint, **kwargs)

    async def open(self) -> None:
        if not self._client:
            self._client = httpx.AsyncClient(**self._client_config)
            await self._client.__aenter__()

    async def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    async def __aenter__(self) -> "APIHttpClient":
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close(exc_type, exc_val, exc_tb)

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        client = self._get_client()

        log.debug(f"Request: {method} {endpoint}")
        log.debug(f"Request kwargs: {kwargs}")

        retryable_method = method.upper() in self._retry.retry_methods
        attempts = self._retry.max_retries + 1 if retryable_method else 1

        for attempt in range(attempts):
            last_attempt = attempt == attempts - 1
            try:
                response = await client.request(method, endpoint, **kwargs)
            except httpx.TimeoutException as e:
                if not last_attempt:
                    await self._sleep_before_retry(attempt, None, method, endpoint)
                    continue
                log.error(f"Request timeout for {method} {endpoint}: {e}")
                raise TimeoutError(f"Request to {endpoint} timed out.") from e
            except httpx.ConnectError as e:
                if not last_attempt:
                    await self._sleep_before_retry(attempt, None, method, endpoint)
                    continue
                log.error(f"Connection error for {method} {endpoint}: {e}")
                raise NetworkError(
                    f"Failed to connect to the API: {e}",
                    original_error=e,
                ) from e
            except httpx.RequestError as e:
                log.error(f"Network error for {method} {endpoint}: {e}")
                raise NetworkError(
                    f"A network error occurred: {e}",
                    original_error=e,
                ) from e

            log.debug(
                f"Response: {response.status_code} {response.reason_phrase} "
                f"for {method} {endpoint}"
            )

            if response.status_code in self._retry.retry_statuses and not last_attempt:
                await self._sleep_before_retry(attempt, response, method, endpoint)
                continue

            raise_for_status(response)
            return response

        raise AssertionError("unreachable: retry loop must return or raise")

    async def _sleep_before_retry(
        self,
        attempt: int,
        response: httpx.Response | None,
        method: str,
        endpoint: str,
    ) -> None:
        delay = None
        if response is not None:
            delay = _parse_retry_after(response.headers.get("Retry-After"))
        if delay is None:
            delay = self._retry.backoff_factor * (2**attempt)
            # Jitter to avoid thundering herds; not security-relevant.
            delay += random.uniform(0, self._retry.backoff_factor / 2)  # nosec B311

        log.debug(
            f"Retrying {method} {endpoint} in {delay:.2f}s "
            f"(attempt {attempt + 1}/{self._retry.max_retries})"
        )
        await asyncio.sleep(delay)
