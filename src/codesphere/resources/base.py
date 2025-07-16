from functools import partial
from typing import Any, Type, List, get_origin, get_args, Optional
from pydantic import BaseModel
from ..client import APIHttpClient


class APIOperation:
    """Describes a single, reusable API operation."""

    def __init__(
        self,
        method: str,
        endpoint_template: str,
        response_model: Type[BaseModel] | Type[List[BaseModel]],
        input_model: Optional[Type[BaseModel]] = None,
    ):
        self.method = method
        self.endpoint_template = endpoint_template
        self.response_model = response_model
        self.input_model = input_model


class ResourceBase:
    """The base class for all resources, containing the logic to execute APIOperations."""

    def __init__(self, http_client: APIHttpClient):
        self._http_client = http_client

    def __getattribute__(self, name: str) -> Any:
        """Intercepts attribute access to execute APIOperations dynamically."""
        attr = super().__getattribute__(name)
        if isinstance(attr, APIOperation):
            return partial(self._execute_operation, operation=attr)
        return attr

    async def _execute_operation(self, operation: APIOperation, **kwargs: Any) -> Any:
        """Executes an APIOperation, fills placeholders, and parses the response."""
        format_args = {**self.__dict__, **kwargs}
        endpoint = operation.endpoint_template.format(**format_args)

        params = kwargs.get("params")
        payload = None

        if operation.input_model:
            input_data = operation.input_model(**kwargs)
            payload = input_data.model_dump()

        response = await self._http_client.request(
            method=operation.method, endpoint=endpoint, json=payload, params=params
        )

        if operation.response_model is None:
            return None

        json_response = response.json()

        origin = get_origin(operation.response_model)
        if origin is list or origin is List:
            item_model = get_args(operation.response_model)[0]
            instances = [item_model.model_validate(item) for item in json_response]
            for instance in instances:
                instance._http_client = self._http_client
            return instances
        else:
            instance = operation.response_model.model_validate(json_response)
            instance._http_client = self._http_client
            return instance
