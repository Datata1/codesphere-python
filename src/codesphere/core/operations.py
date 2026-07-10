from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

ResponseT = TypeVar("ResponseT")
InputT = TypeVar("InputT")
EntryT = TypeVar("EntryT")

type AsyncCallable[_T] = Callable[[], Awaitable[_T]]


class APIOperation(BaseModel, Generic[ResponseT, InputT]):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    method: str
    endpoint_template: str
    response_model: type[ResponseT]
    input_model: type[InputT] | None = None


class StreamOperation(BaseModel, Generic[EntryT]):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    endpoint_template: str
    entry_model: type[EntryT]
