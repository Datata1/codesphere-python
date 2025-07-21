import pytest
import httpx
from unittest.mock import patch, AsyncMock
from dataclasses import dataclass
from typing import Optional, Any, Type
from pydantic import BaseModel

from codesphere.client import APIHttpClient, AuthenticationError


class DummyModel(BaseModel):
    """Ein einfaches Pydantic-Modell für Testzwecke."""

    name: str
    value: int


@dataclass
class InitTestCase:
    """Definiert einen Testfall für die Initialisierung des APIHttpClient."""

    name: str
    token_env_var: Optional[str]
    expected_exception: Optional[Type[Exception]] = None


@dataclass
class RequestTestCase:
    """Definiert einen Testfall für die Request-Methoden des APIHttpClient."""

    name: str
    method: str
    use_context_manager: bool
    payload: Any = None
    mock_status_code: int = 200
    expected_exception: Optional[Type[Exception]] = None


init_test_cases = [
    InitTestCase(
        name="Erfolgreiche Initialisierung mit Token",
        token_env_var="secret-token",
        expected_exception=None,
    ),
    InitTestCase(
        name="Fehlgeschlagene Initialisierung ohne Token",
        token_env_var=None,
        expected_exception=AuthenticationError,
    ),
]

request_test_cases = [
    RequestTestCase(
        name="GET-Request erfolgreich",
        method="get",
        use_context_manager=True,
    ),
    RequestTestCase(
        name="POST-Request mit Pydantic-Modell erfolgreich",
        method="post",
        use_context_manager=True,
        payload=DummyModel(name="test", value=123),
    ),
    RequestTestCase(
        name="PUT-Request mit Dictionary erfolgreich",
        method="put",
        use_context_manager=True,
        payload={"key": "value"},
    ),
    RequestTestCase(
        name="Request schlägt fehl ohne Context Manager",
        method="get",
        use_context_manager=False,
        expected_exception=RuntimeError,
    ),
    RequestTestCase(
        name="Request mit 404-Fehler löst HTTPStatusError aus",
        method="get",
        use_context_manager=True,
        mock_status_code=404,
        expected_exception=httpx.HTTPStatusError,
    ),
    RequestTestCase(
        name="Request mit 500-Fehler löst HTTPStatusError aus",
        method="post",
        use_context_manager=True,
        mock_status_code=500,
        expected_exception=httpx.HTTPStatusError,
    ),
]


@pytest.mark.parametrize("case", init_test_cases, ids=[c.name for c in init_test_cases])
def test_client_initialization(case: InitTestCase):
    """
    Testet die Initialisierungslogik des APIHttpClient.
    """
    with patch("os.environ.get", return_value=case.token_env_var):
        if case.expected_exception:
            with pytest.raises(case.expected_exception):
                APIHttpClient()
        else:
            client = APIHttpClient()
            assert client._token == case.token_env_var


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case", request_test_cases, ids=[c.name for c in request_test_cases]
)
async def test_client_requests(case: RequestTestCase):
    """
    Testet die verschiedenen Request-Methoden (get, post, etc.) und deren Verhalten.
    """
    with patch("os.environ.get", return_value="fake-token"):
        client = APIHttpClient()

        mock_http_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = case.mock_status_code

        if 400 <= case.mock_status_code < 600:
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"{case.mock_status_code} Error",
                request=AsyncMock(),
                response=mock_response,
            )

        mock_http_client.request.return_value = mock_response

        if case.expected_exception:
            with pytest.raises(case.expected_exception):
                with patch("httpx.AsyncClient", return_value=mock_http_client):
                    if case.use_context_manager:
                        async with client:
                            await getattr(client, case.method)("/test-endpoint")
                    else:
                        await getattr(client, case.method)("/test-endpoint")
            return

        with patch("httpx.AsyncClient", return_value=mock_http_client):
            async with client:
                request_func = getattr(client, case.method)
                response = await request_func("/test-endpoint", json=case.payload)

                mock_http_client.request.assert_awaited_once()
                call_args = mock_http_client.request.call_args
                assert call_args.args[0] == case.method.upper()
                assert call_args.args[1] == "/test-endpoint"

                if isinstance(case.payload, BaseModel):
                    assert call_args.kwargs["json"] == case.payload.model_dump(
                        exclude_none=True
                    )
                else:
                    assert call_args.kwargs["json"] == case.payload

                assert response.status_code == case.mock_status_code
