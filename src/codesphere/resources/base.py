from ..cs_types.rest.http_client import APIHttpClient
from ..cs_types.rest.handler import _APIOperationExecutor


class ResourceBase(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient):
        self._http_client = http_client
