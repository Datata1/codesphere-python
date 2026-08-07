from dataclasses import dataclass

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_BASE_URL = "https://codesphere.com/api"


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Retry behavior for transient failures.

    Enabled by default (``max_retries=2``); set ``max_retries=0`` to disable.
    Requests using a method in ``retry_methods`` are retried on the statuses
    in ``retry_statuses`` and on connect/timeout errors. The delay honors a
    ``Retry-After`` response header (seconds or HTTP-date) when present,
    otherwise exponential backoff with jitter is used. Only idempotent
    methods are retried by default; add ``"POST"`` to ``retry_methods``
    explicitly if your endpoints tolerate it.

    Retries and duplicate side effects
    ----------------------------------
    ``PUT`` and ``DELETE`` are idempotent as HTTP methods, but not always
    in effect. When the first attempt reaches the platform and only its
    response is lost (a gateway 503, a dropped connection), the retry runs
    the operation a second time — a landscape teardown, for example, can
    execute twice. The Codesphere API has no idempotency keys, so the SDK
    cannot deduplicate this for you.

    The SDK does handle the most common consequence: a 404 on a retried
    ``DELETE`` is treated as success, because the resource being gone is
    what the caller asked for. A 404 on the *first* attempt still raises
    :class:`~codesphere.NotFoundError`.

    If duplicate execution is unacceptable for your workload, set
    ``max_retries=0`` or drop the method from ``retry_methods``.
    """

    max_retries: int = 2
    backoff_factor: float = 0.5
    retry_statuses: frozenset[int] = frozenset({429, 502, 503, 504})
    retry_methods: frozenset[str] = frozenset({"GET", "HEAD", "PUT", "DELETE"})


class Settings(BaseSettings):
    """Environment-driven defaults (``CS_*`` variables, optional ``.env``).

    Constructed lazily by :class:`codesphere.CodesphereSDK` — importing the
    package never requires any environment variable to be set.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CS_",
        extra="ignore",
    )

    token: SecretStr | None = None
    base_url: HttpUrl = HttpUrl(DEFAULT_BASE_URL)

    client_timeout_connect: float = 10.0
    client_timeout_read: float = 30.0
