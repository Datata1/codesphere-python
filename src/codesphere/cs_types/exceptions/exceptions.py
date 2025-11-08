class CodesphereError(Exception):
    """Base exception class for all errors in the Codesphere SDK."""

    pass


class AuthenticationError(CodesphereError):
    """Raised for authentication-related errors, like a missing API token."""

    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Authentication token not provided. Please pass it as an argument "
                "or set the 'CS_TOKEN' environment variable."
            )
        super().__init__(message)
