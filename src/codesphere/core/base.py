from typing import Generic, List, TypeVar
from pydantic import BaseModel, ConfigDict, RootModel
from pydantic.alias_generators import to_camel

from ..http_client import APIHttpClient
from .handler import _APIOperationExecutor

ModelT = TypeVar("ModelT")


class ResourceBase(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient):
        self._http_client = http_client


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ResourceList(RootModel[List[ModelT]], Generic[ModelT]):
    root: List[ModelT]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)
