from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

ResponseT = TypeVar("ResponseT")
EntryT = TypeVar("EntryT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class APIOperation(Generic[ResponseT]):
    """Declarative description of a single API endpoint.

    ``response_model`` drives both response validation and the static return
    type of ``_execute``: use a pydantic model class (``ResourceList[Team]``
    included) or ``types.NoneType`` for endpoints without a response body.
    ``input_model``, when set, validates the ``data`` payload before the
    request is sent.
    """

    method: str
    endpoint_template: str
    response_model: type[ResponseT]
    input_model: type[BaseModel] | None = None


@dataclass(frozen=True, slots=True)
class StreamOperation(Generic[EntryT]):
    """Declarative description of an SSE streaming endpoint."""

    endpoint_template: str
    entry_model: type[EntryT]
