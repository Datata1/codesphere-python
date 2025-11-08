from typing import Callable, Awaitable, List, Optional, Type, TypeAlias, TypeVar

from pydantic import BaseModel


_T = TypeVar("_T")

AsyncCallable: TypeAlias = Callable[[], Awaitable[_T]]


class APIOperation:
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
