# Configuration & errors

## Retry configuration

::: codesphere.RetryConfig

## Exceptions

::: codesphere.exceptions
    options:
      show_root_heading: false
      members:
        - CodesphereError
        - APIError
        - AuthenticationError
        - AuthorizationError
        - NotFoundError
        - ValidationError
        - ConflictError
        - RateLimitError
        - NetworkError
        - TimeoutError
        - FeatureFlagError
        - FeatureNotAvailableError
        - FeatureNotEnabledError
