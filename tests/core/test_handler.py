import pytest
from typing import Optional, List
from unittest.mock import MagicMock

from pydantic import BaseModel, Field, PrivateAttr, RootModel

from codesphere.core.handler import _APIOperationExecutor, APIRequestHandler
from codesphere.core.operations import APIOperation, AsyncCallable


class SampleResponseModel(BaseModel):
    id: int
    name: str


class SampleInputModel(BaseModel):
    title: str
    count: int


class ConcreteExecutor(_APIOperationExecutor, BaseModel):
    id: int = 100
    _http_client: Optional[MagicMock] = PrivateAttr(default=None)


class TestAPIOperationExecutor:
    def test_http_client_private_attribute_exists(self):
        executor = ConcreteExecutor()
        assert hasattr(executor, "_http_client")
        executor._http_client = MagicMock()
        assert executor._http_client is not None

    def test_getattribute_returns_partial_for_operation(self):
        class ExecutorWithOp(_APIOperationExecutor, BaseModel):
            id: int = 123
            _http_client: Optional[MagicMock] = PrivateAttr(default=None)
            test_op: AsyncCallable[SampleResponseModel] = Field(
                default=APIOperation(
                    method="GET",
                    endpoint_template="/test/{id}",
                    response_model=SampleResponseModel,
                ),
                exclude=True,
            )

        executor = ExecutorWithOp()
        attr = executor.test_op
        assert callable(attr)

    def test_getattribute_returns_normal_values(self):
        class SampleExecutor(_APIOperationExecutor, BaseModel):
            id: int = 456
            name: str = "test"
            _http_client: Optional[MagicMock] = PrivateAttr(default=None)

        executor = SampleExecutor()
        assert executor.id == 456
        assert executor.name == "test"


class TestAPIRequestHandler:
    @pytest.fixture
    def mock_executor(self):
        executor = ConcreteExecutor()
        mock_client = MagicMock()
        mock_client.request = MagicMock()
        executor._http_client = mock_client
        return executor

    @pytest.fixture
    def sample_operation(self):
        return APIOperation(
            method="GET",
            endpoint_template="/resources/{id}",
            response_model=SampleResponseModel,
        )

    def test_handler_initialization(self, mock_executor, sample_operation):
        kwargs = {"param": "value"}
        handler = APIRequestHandler(
            executor=mock_executor,
            operation=sample_operation,
            kwargs=kwargs,
        )
        assert handler.executor is mock_executor
        assert handler.operation is sample_operation
        assert handler.kwargs == kwargs
        assert handler.http_client is mock_executor._http_client

    def test_prepare_request_args_formats_endpoint(
        self, mock_executor, sample_operation
    ):
        handler = APIRequestHandler(
            executor=mock_executor,
            operation=sample_operation,
            kwargs={},
        )
        endpoint, request_kwargs = handler._prepare_request_args()
        assert endpoint == "/resources/100"

    def test_prepare_request_args_with_data_payload(self, mock_executor):
        operation = APIOperation(
            method="POST",
            endpoint_template="/resources",
            response_model=SampleResponseModel,
            input_model=SampleInputModel,
        )
        input_model = SampleInputModel(title="Test", count=10)
        handler = APIRequestHandler(
            executor=mock_executor,
            operation=operation,
            kwargs={"data": input_model},
        )
        endpoint, request_kwargs = handler._prepare_request_args()
        assert "json" in request_kwargs
        assert request_kwargs["json"] == {"title": "Test", "count": 10}

    @pytest.mark.asyncio
    async def test_execute_raises_without_http_client(self, sample_operation):
        executor = ConcreteExecutor()
        handler = APIRequestHandler(
            executor=executor,
            operation=sample_operation,
            kwargs={},
        )
        with pytest.raises(
            RuntimeError, match="Cannot access resource on a detached model"
        ):
            await handler.execute()

    @pytest.mark.asyncio
    async def test_inject_client_into_model(self, mock_executor, sample_operation):
        mock_client = MagicMock()
        mock_client.request = MagicMock()
        mock_executor._http_client = mock_client

        handler = APIRequestHandler(
            executor=mock_executor,
            operation=sample_operation,
            kwargs={},
        )

        class ModelWithClient(BaseModel):
            id: int
            _http_client: Optional[MagicMock] = PrivateAttr(default=None)

        instance = ModelWithClient(id=1)
        handler._inject_client_into_model(instance)
        assert instance._http_client is mock_executor._http_client

    @pytest.mark.asyncio
    async def test_inject_client_into_root_model_items(
        self, mock_executor, sample_operation
    ):
        """RootModel containers should have _http_client injected into each item in .root"""
        mock_client = MagicMock()
        mock_client.request = MagicMock()
        mock_executor._http_client = mock_client

        handler = APIRequestHandler(
            executor=mock_executor,
            operation=sample_operation,
            kwargs={},
        )

        class ItemWithClient(BaseModel):
            id: int
            _http_client: Optional[MagicMock] = PrivateAttr(default=None)

        class ResourceList(RootModel[List[ItemWithClient]]):
            _http_client: Optional[MagicMock] = PrivateAttr(default=None)

        item1 = ItemWithClient(id=1)
        item2 = ItemWithClient(id=2)
        resource_list = ResourceList(root=[item1, item2])

        handler._inject_client_into_model(resource_list)

        assert resource_list._http_client is mock_executor._http_client
        for item in resource_list.root:
            assert item._http_client is mock_executor._http_client
