from types import NoneType
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, ValidationError

from codesphere.core.base import BoundModel, ResourceBase, ResourceList
from codesphere.core.handler import execute_operation
from codesphere.core.operations import APIOperation


class SampleResponseModel(BaseModel):
    id: int
    name: str


class SampleInputModel(BaseModel):
    title: str
    count: int


class SampleBoundModel(BoundModel):
    id: int


def make_client(json_data=None):
    """Mock APIHttpClient whose request returns a response with json_data."""
    response = MagicMock()
    response.json.return_value = json_data if json_data is not None else {}
    client = MagicMock()
    client.request = AsyncMock(return_value=response)
    return client


GET_OP = APIOperation(
    method="GET",
    endpoint_template="/resources/{id}",
    response_model=SampleResponseModel,
)

CREATE_OP = APIOperation(
    method="POST",
    endpoint_template="/resources",
    input_model=SampleInputModel,
    response_model=SampleResponseModel,
)

DELETE_OP = APIOperation(
    method="DELETE",
    endpoint_template="/resources/{id}",
    response_model=NoneType,
)


class TestExecuteOperation:
    async def test_formats_endpoint_from_path_params(self):
        client = make_client({"id": 1, "name": "x"})
        await execute_operation(client, GET_OP, path_params={"id": 100})

        call = client.request.call_args
        assert call.kwargs["method"] == "GET"
        assert call.kwargs["endpoint"] == "/resources/100"

    async def test_missing_path_param_raises_before_request(self):
        client = make_client()
        with pytest.raises(ValueError, match="Missing path parameter 'id'"):
            await execute_operation(client, GET_OP)
        client.request.assert_not_awaited()

    async def test_model_payload_is_dumped(self):
        client = make_client({"id": 1, "name": "x"})
        payload = SampleInputModel(title="Test", count=10)
        await execute_operation(client, CREATE_OP, data=payload)

        call = client.request.call_args
        assert call.kwargs["json"] == {"title": "Test", "count": 10}

    async def test_dict_payload_is_validated_against_input_model(self):
        client = make_client({"id": 1, "name": "x"})
        await execute_operation(client, CREATE_OP, data={"title": "Test", "count": 10})

        call = client.request.call_args
        assert call.kwargs["json"] == {"title": "Test", "count": 10}

    async def test_invalid_payload_rejected_before_request(self):
        client = make_client()
        with pytest.raises(ValidationError):
            await execute_operation(client, CREATE_OP, data={"title": "no count"})
        client.request.assert_not_awaited()

    async def test_empty_dict_body_is_sent(self):
        """Regression: falsy payloads must still be sent as the JSON body."""
        op = APIOperation(
            method="PATCH",
            endpoint_template="/resources/{id}",
            response_model=NoneType,
        )
        client = make_client()
        await execute_operation(client, op, data={}, path_params={"id": 1})

        call = client.request.call_args
        assert call.kwargs["json"] == {}

    async def test_no_data_sends_no_json_kwarg(self):
        client = make_client({"id": 1, "name": "x"})
        await execute_operation(client, GET_OP, path_params={"id": 1})

        call = client.request.call_args
        assert "json" not in call.kwargs

    async def test_params_are_passed_through(self):
        client = make_client({"id": 1, "name": "x"})
        await execute_operation(
            client, GET_OP, params={"limit": 5}, path_params={"id": 1}
        )

        call = client.request.call_args
        assert call.kwargs["params"] == {"limit": 5}

    async def test_none_response_model_returns_none(self):
        client = make_client()
        result = await execute_operation(client, DELETE_OP, path_params={"id": 1})
        assert result is None
        client.request.return_value.json.assert_not_called()

    async def test_response_is_validated_into_model(self):
        client = make_client({"id": 7, "name": "seven"})
        result = await execute_operation(client, GET_OP, path_params={"id": 7})

        assert isinstance(result, SampleResponseModel)
        assert result.id == 7
        assert result.name == "seven"

    async def test_invalid_response_raises_validation_error(self):
        client = make_client({"unexpected": "shape"})
        with pytest.raises(ValidationError):
            await execute_operation(client, GET_OP, path_params={"id": 1})

    async def test_client_is_bound_to_returned_model(self):
        op = APIOperation(
            method="GET",
            endpoint_template="/bound/{id}",
            response_model=SampleBoundModel,
        )
        client = make_client({"id": 1})
        result = await execute_operation(client, op, path_params={"id": 1})

        assert result._http_client is client

    async def test_client_is_bound_to_resource_list_items(self):
        op = APIOperation(
            method="GET",
            endpoint_template="/bound",
            response_model=ResourceList[SampleBoundModel],
        )
        client = make_client([{"id": 1}, {"id": 2}])
        result = await execute_operation(client, op)

        assert len(result) == 2
        for item in result:
            assert item._http_client is client


class TestResourceBaseExecute:
    async def test_execute_uses_stored_client_and_kwargs_as_path_params(self):
        client = make_client({"id": 1, "name": "x"})
        resource = ResourceBase(http_client=client)

        result = await resource._execute(GET_OP, id=42)

        assert isinstance(result, SampleResponseModel)
        assert client.request.call_args.kwargs["endpoint"] == "/resources/42"


class TestBoundModelExecute:
    async def test_detached_model_raises(self):
        model = SampleBoundModel(id=1)
        with pytest.raises(
            RuntimeError, match="Cannot access resource on a detached model"
        ):
            await model._execute(DELETE_OP, id=1)

    async def test_bound_model_executes_with_attached_client(self):
        client = make_client()
        model = SampleBoundModel(id=1)
        model._http_client = client

        await model._execute(DELETE_OP, id=model.id)

        assert client.request.call_args.kwargs["endpoint"] == "/resources/1"


class TestClientBindingHelpers:
    def test_bind_client_sets_bound_model(self):
        from codesphere.core.handler import _bind_client

        client = MagicMock()
        instance = SampleBoundModel(id=1)
        _bind_client(instance, client)
        assert instance._http_client is client

    def test_bind_client_ignores_plain_models(self):
        from codesphere.core.handler import _bind_client

        instance = SampleResponseModel(id=1, name="x")
        _bind_client(instance, MagicMock())  # must not raise

    def test_bind_client_sets_root_model_items(self):
        from codesphere.core.handler import _bind_client

        client = MagicMock()
        items = ResourceList[SampleBoundModel](
            root=[SampleBoundModel(id=1), SampleBoundModel(id=2)]
        )
        _bind_client(items, client)
        for item in items:
            assert item._http_client is client
