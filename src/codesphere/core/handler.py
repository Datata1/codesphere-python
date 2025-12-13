from functools import partial
import logging
from typing import Any, List, Optional, Type, get_args, get_origin

import httpx
from pydantic import BaseModel, PrivateAttr, ValidationError
from pydantic.fields import FieldInfo

from ..http_client import APIHttpClient
from .operations import APIOperation

log = logging.getLogger(__name__)


class _APIOperationExecutor:
    _http_client: Optional[APIHttpClient] = PrivateAttr(default=None)

    def __getattribute__(self, name: str) -> Any:
        attr = super().__getattribute__(name)
        operation = None

        if isinstance(attr, FieldInfo):
            if isinstance(attr.default, APIOperation):
                operation = attr.default
        elif isinstance(attr, APIOperation):
            operation = attr

        if operation:
            return partial(self._execute_operation, operation=operation)

        return attr

    async def _execute_operation(self, operation: APIOperation, **kwargs: Any) -> Any:
        handler = APIRequestHandler(executor=self, operation=operation, kwargs=kwargs)
        return await handler.execute()


class APIRequestHandler:
    def __init__(
        self, executor: _APIOperationExecutor, operation: APIOperation, kwargs: dict
    ):
        self.executor = executor
        self.operation = operation
        self.kwargs = kwargs
        self.http_client = executor._http_client

    async def execute(self) -> Any:
        endpoint, request_kwargs = self._prepare_request_args()

        response = await self._make_request(
            self.operation.method, endpoint, **request_kwargs
        )

        return await self._parse_and_validate_response(
            response, self.operation.response_model, endpoint
        )

    def _prepare_request_args(self) -> tuple[str, dict]:
        format_args = {}
        format_args.update(self.kwargs)
        format_args.update(self.executor.__dict__)
        if isinstance(self.executor, BaseModel):
            format_args.update(self.executor.model_dump())
        format_args.update(self.kwargs)

        endpoint = self.operation.endpoint_template.format(**format_args)

        payload = None
        if json_data_obj := self.kwargs.get("data"):
            if isinstance(json_data_obj, BaseModel):
                payload = json_data_obj.model_dump(exclude_none=True)
            else:
                payload = json_data_obj

        if payload is not None:
            log.info(f"PAYLOAD TYPE: {type(payload)}")
            log.info(f"PAYLOAD CONTENT: {payload}")

        request_kwargs = {"params": self.kwargs.get("params"), "json": payload}
        return endpoint, {k: v for k, v in request_kwargs.items() if v is not None}

    async def _make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        if not self.http_client:
            raise RuntimeError("HTTP Client is not initialized.")
        return await self.http_client.request(
            method=method, endpoint=endpoint, **kwargs
        )

    def _inject_client_into_model(self, model_instance: BaseModel) -> BaseModel:
        if hasattr(model_instance, "_http_client"):
            model_instance._http_client = self.http_client
        return model_instance

    async def _parse_and_validate_response(
        self,
        response: httpx.Response,
        response_model: Type[BaseModel] | Type[List[BaseModel]] | None,
        endpoint_for_logging: str,
    ) -> Any:
        if response_model is None:
            return None

        try:
            json_response = response.json()
            log.debug(f"Validating JSON response for endpoint: {endpoint_for_logging}")
        except httpx.ResponseNotRead:
            log.warning(f"No JSON response body for {endpoint_for_logging}")
            return None

        try:
            origin = get_origin(response_model)
            if origin is list or origin is List:
                item_model = get_args(response_model)[0]
                instances = [item_model.model_validate(item) for item in json_response]
                for instance in instances:
                    self._inject_client_into_model(instance)
                log.debug("Successfully validated response into list of models.")
                return instances
            else:
                instance = response_model.model_validate(json_response)
                self._inject_client_into_model(instance)
                log.debug("Successfully validated response into single model.")
                return instance
        except ValidationError as e:
            log.error(
                f"Pydantic validation failed for {endpoint_for_logging}. Error: {e}"
            )
            log.error(f"Failing JSON data: {json_response}")
            raise e
