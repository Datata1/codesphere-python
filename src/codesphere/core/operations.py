from typing import Callable, Awaitable, Generic, Optional, Type, TypeAlias, TypeVar

from pydantic import BaseModel


_T = TypeVar("_T")
ResponseT = TypeVar("ResponseT")
InputT = TypeVar("InputT")

AsyncCallable: TypeAlias = Callable[[], Awaitable[_T]]


class APIOperation(BaseModel, Generic[ResponseT, InputT]):
    method: str
    endpoint_template: str
    response_model: Type[ResponseT]
    input_model: Optional[Type[InputT]] = None
