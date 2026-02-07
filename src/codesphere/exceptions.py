from typing import Any, Optional

import httpx


class CodesphereError(Exception):
    """Base exception class for all errors in the Codesphere SDK.

    All SDK exceptions inherit from this, so users can catch this
    to handle any SDK-related error.
    """

    def __init__(self, message: str = "An error occurred in the Codesphere SDK."):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(CodesphereError):
    """Raised for authentication-related errors, like a missing or invalid API token.

    HTTP Status: 401
    """

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = (
                "Authentication token not provided or invalid. Please pass it as an argument "
                "or set the 'CS_TOKEN' environment variable."
            )
        super().__init__(message)


class AuthorizationError(CodesphereError):
    """Raised when the user doesn't have permission to perform an action.

    HTTP Status: 403
    """

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = "You don't have permission to perform this action."
        super().__init__(message)


class NotFoundError(CodesphereError):
    """Raised when the requested resource does not exist.

    HTTP Status: 404
    """

    def __init__(self, message: Optional[str] = None, resource: Optional[str] = None):
        self.resource = resource
        if message is None:
            if resource:
                message = f"The requested {resource} was not found."
            else:
                message = "The requested resource was not found."
        super().__init__(message)


class ValidationError(CodesphereError):
    """Raised when the request data is invalid or malformed.

    HTTP Status: 400, 422
    """

    def __init__(
        self,
        message: Optional[str] = None,
        errors: Optional[list[dict[str, Any]]] = None,
    ):
        self.errors = errors or []
        if message is None:
            message = "The request data was invalid."
        super().__init__(message)


class ConflictError(CodesphereError):
    """Raised when there's a conflict with the current state of a resource.

    HTTP Status: 409
    """

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = "The request conflicts with the current state of the resource."
        super().__init__(message)


class RateLimitError(CodesphereError):
    """Raised when rate limits are exceeded.

    HTTP Status: 429
    """

    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        self.retry_after = retry_after
        if message is None:
            if retry_after:
                message = f"Rate limit exceeded. Retry after {retry_after} seconds."
            else:
                message = "Rate limit exceeded. Please slow down your requests."
        super().__init__(message)


class APIError(CodesphereError):
    """Raised for general API errors that don't fit other categories.

    Contains detailed information about the failed request.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
        request_url: Optional[str] = None,
        request_method: Optional[str] = None,
    ):
        self.status_code = status_code
        self.response_body = response_body
        self.request_url = request_url
        self.request_method = request_method

        if message is None:
            message = f"API request failed with status {status_code}."
        super().__init__(message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.request_method and self.request_url:
            parts.append(f"Request: {self.request_method} {self.request_url}")
        return " | ".join(parts)


class NetworkError(CodesphereError):
    """Raised for network-related issues like connection failures or timeouts."""

    def __init__(
        self, message: Optional[str] = None, original_error: Optional[Exception] = None
    ):
        self.original_error = original_error
        if message is None:
            message = "A network error occurred while connecting to the API."
        super().__init__(message)


class TimeoutError(NetworkError):
    """Raised when a request times out."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = "The request timed out. The server may be slow or unavailable."
        super().__init__(message)


def raise_for_status(response: httpx.Response) -> None:
    """Convert HTTP errors to appropriate SDK exceptions.

    This function should be called after every API request to translate
    HTTP errors into user-friendly SDK exceptions.

    Args:
        response: The httpx Response object to check.

    Raises:
        AuthenticationError: For 401 responses.
        AuthorizationError: For 403 responses.
        NotFoundError: For 404 responses.
        ValidationError: For 400/422 responses.
        ConflictError: For 409 responses.
        RateLimitError: For 429 responses.
        APIError: For other 4xx/5xx responses.
    """
    if response.is_success:
        return

    status_code = response.status_code

    error_message = None
    response_body = None
    try:
        response_body = response.json()
        error_message = (
            response_body.get("message")
            or response_body.get("error")
            or response_body.get("detail")
            or response_body.get("errors")
        )
        if isinstance(error_message, list):
            error_message = "; ".join(str(e) for e in error_message)
    except Exception:
        error_message = response.text or None

    request_url = str(response.request.url) if response.request else None
    request_method = response.request.method if response.request else None

    if status_code == 401:
        raise AuthenticationError(error_message)
    elif status_code == 403:
        raise AuthorizationError(error_message)
    elif status_code == 404:
        raise NotFoundError(error_message)
    elif status_code in (400, 422):
        errors = (
            response_body.get("errors") if isinstance(response_body, dict) else None
        )
        raise ValidationError(error_message, errors=errors)
    elif status_code == 409:
        raise ConflictError(error_message)
    elif status_code == 429:
        retry_after = response.headers.get("Retry-After")
        retry_after_int = (
            int(retry_after) if retry_after and retry_after.isdigit() else None
        )
        raise RateLimitError(error_message, retry_after=retry_after_int)
    else:
        raise APIError(
            message=error_message,
            status_code=status_code,
            response_body=response_body,
            request_url=request_url,
            request_method=request_method,
        )
