# Configuration

Every option can be passed directly to the constructor:

```python
from codesphere import CodesphereSDK

sdk = CodesphereSDK(token="your-api-token")
# or, e.g. against a different deployment:
sdk = CodesphereSDK(
    token="your-api-token",
    base_url="https://my-instance.example.com/api",
)
```

Alternatively, configure via environment variables (or a `.env` file in your
project root). Explicit constructor arguments always win over the environment:

| Variable | Description | Default |
|----------|-------------|---------|
| `CS_TOKEN` | API token (required) | – |
| `CS_BASE_URL` | API base URL | `https://codesphere.com/api` |
| `CS_CLIENT_TIMEOUT_CONNECT` | Connect timeout in seconds | `10.0` |
| `CS_CLIENT_TIMEOUT_READ` | Read timeout in seconds | `30.0` |

If no token is provided at all, `CodesphereSDK()` raises an
`AuthenticationError` at construction (importing the package never requires
any environment variable).

## Client lifecycle

The client owns an HTTP connection pool. Use it as an async context manager
(recommended) or open/close it explicitly:

```python
async with CodesphereSDK() as sdk:
    ...

# or
sdk = CodesphereSDK()
await sdk.open()
try:
    ...
finally:
    await sdk.close()
```

## Logging

The SDK logs to the `codesphere` logger (a `NullHandler` is installed by
default). Enable debug output to see requests, responses, and retries:

```python
import logging

logging.getLogger("codesphere").setLevel(logging.DEBUG)
logging.basicConfig()
```

Request and response bodies are never logged — payloads such as env-var
values can contain secrets.
