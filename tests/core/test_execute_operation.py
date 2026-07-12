"""Executor behavior tests at the real HTTP boundary (respx).

Unlike tests/core/test_handler.py (which unit-tests against a mocked
APIHttpClient), these drive execute_operation through the actual httpx
transport: URL building, headers, body encoding, and response parsing
are all real.
"""

import json
from types import NoneType

import pytest
from pydantic import BaseModel, ValidationError

from codesphere.core.base import BoundModel, ResourceBase, ResourceList
from codesphere.core.operations import APIOperation


class Thing(BoundModel):
    id: int
    name: str

    async def rename(self, name: str) -> None:
        await self._execute(RENAME_THING, thing_id=self.id, data={"name": name})


class ThingCreate(BaseModel):
    name: str
    size: int


GET_THING = APIOperation(
    method="GET", endpoint_template="/things/{thing_id}", response_model=Thing
)
LIST_THINGS = APIOperation(
    method="GET", endpoint_template="/things", response_model=ResourceList[Thing]
)
CREATE_THING = APIOperation(
    method="POST",
    endpoint_template="/things",
    input_model=ThingCreate,
    response_model=Thing,
)
RENAME_THING = APIOperation(
    method="PATCH", endpoint_template="/things/{thing_id}", response_model=NoneType
)


class ThingsResource(ResourceBase):
    async def get(self, thing_id: int) -> Thing:
        return await self._execute(GET_THING, thing_id=thing_id)

    async def list(self) -> list[Thing]:
        return (await self._execute(LIST_THINGS)).root

    async def create(self, payload) -> Thing:
        return await self._execute(CREATE_THING, data=payload)

    async def rename(self, thing_id: int, data) -> None:
        await self._execute(RENAME_THING, thing_id=thing_id, data=data)


@pytest.fixture
def things(sdk):
    return ThingsResource(sdk._http_client)


class TestRequestConstruction:
    async def test_path_params_format_the_real_url(self, things, mock_api):
        route = mock_api.get("/things/42").respond(200, json={"id": 42, "name": "x"})
        await things.get(thing_id=42)
        assert route.called

    async def test_auth_header_reaches_the_wire(self, things, mock_api):
        route = mock_api.get("/things/1").respond(200, json={"id": 1, "name": "x"})
        await things.get(thing_id=1)
        request = route.calls.last.request
        assert request.headers["authorization"] == "Bearer test-token"

    async def test_model_payload_is_serialized(self, things, mock_api):
        route = mock_api.post("/things").respond(201, json={"id": 1, "name": "a"})
        await things.create(ThingCreate(name="a", size=3))
        assert json.loads(route.calls.last.request.content) == {"name": "a", "size": 3}

    async def test_dict_payload_is_validated_against_input_model(
        self, things, mock_api
    ):
        route = mock_api.post("/things").respond(201, json={"id": 1, "name": "a"})
        await things.create({"name": "a", "size": 3})
        assert json.loads(route.calls.last.request.content) == {"name": "a", "size": 3}

    async def test_invalid_payload_never_reaches_the_wire(self, things, mock_api):
        route = mock_api.post("/things").respond(201, json={})
        with pytest.raises(ValidationError):
            await things.create({"name": "missing size"})
        assert not route.called

    async def test_empty_dict_body_is_sent(self, things, mock_api):
        """Regression: falsy payloads must still be sent as the JSON body."""
        route = mock_api.patch("/things/1").respond(204)
        await things.rename(1, data={})
        assert route.calls.last.request.content == b"{}"


class TestResponseHandling:
    async def test_response_is_validated_into_model(self, things, mock_api):
        mock_api.get("/things/7").respond(200, json={"id": 7, "name": "seven"})
        thing = await things.get(thing_id=7)
        assert isinstance(thing, Thing)
        assert thing.name == "seven"

    async def test_none_response_model_returns_none(self, things, mock_api):
        mock_api.patch("/things/1").respond(204)
        assert await things.rename(1, data={"name": "n"}) is None

    async def test_invalid_response_shape_raises(self, things, mock_api):
        mock_api.get("/things/1").respond(200, json={"unexpected": True})
        with pytest.raises(ValidationError):
            await things.get(thing_id=1)

    async def test_list_items_are_bound_and_can_make_calls(self, things, mock_api):
        mock_api.get("/things").respond(
            200, json=[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        )
        rename_route = mock_api.patch("/things/2").respond(204)

        items = await things.list()
        await items[1].rename("renamed")

        assert rename_route.called
        assert json.loads(rename_route.calls.last.request.content) == {
            "name": "renamed"
        }
