from ..http_client import APIHttpClient
from .handler import _APIOperationExecutor


class ResourceBase(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient):
        self._http_client = http_client
