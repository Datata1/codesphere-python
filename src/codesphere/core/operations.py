from typing import Awaitable, Callable, Generic, Optional, Type, TypeAlias, TypeVar

from pydantic import BaseModel, ConfigDict

_T = TypeVar("_T")
ResponseT = TypeVar("ResponseT")
InputT = TypeVar("InputT")
EntryT = TypeVar("EntryT")

AsyncCallable: TypeAlias = Callable[[], Awaitable[_T]]


class APIOperation(BaseModel, Generic[ResponseT, InputT]):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    method: str
    endpoint_template: str
    response_model: Type[ResponseT]
    input_model: Optional[Type[InputT]] = None


class StreamOperation(BaseModel, Generic[EntryT]):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    endpoint_template: str
    entry_model: Type[EntryT]
