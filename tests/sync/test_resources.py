"""Resource-layer behavior of the sync client at the HTTP boundary."""

import json

import pytest

import codesphere
from codesphere import FeatureNotEnabledError, NotFoundError
from codesphere.sync import WorkspaceCreate


class TestResources:
    def test_teams_list(self, sdk, mock_api, sample_team_json):
        route = mock_api.get("/teams").respond(200, json=[sample_team_json])
        teams = sdk.teams.list()
        assert [t.name for t in teams] == ["Team"]
        assert route.called

    def test_bound_model_entity_method(self, sdk, mock_api, sample_workspace_json):
        mock_api.get("/workspaces/5").respond(200, json=sample_workspace_json)
        delete_route = mock_api.delete("/workspaces/5").respond(204)

        workspace = sdk.workspaces.get(5)
        workspace.delete()

        assert delete_route.called

    def test_cached_property_sub_manager(self, sdk, mock_api, sample_workspace_json):
        mock_api.get("/workspaces/5").respond(200, json=sample_workspace_json)
        env_route = mock_api.get("/workspaces/5/env-vars").respond(
            200, json=[{"name": "A", "value": "b"}]
        )

        workspace = sdk.workspaces.get(5)
        env_vars = workspace.env_vars.get()

        assert [e.name for e in env_vars] == ["A"]
        assert env_route.called

    def test_error_mapping(self, sdk, mock_api):
        mock_api.get("/workspaces/404").respond(404, json={"message": "nope"})
        with pytest.raises(NotFoundError):
            sdk.workspaces.get(404)

    def test_per_call_timeout_reaches_the_wire(
        self, sdk, mock_api, sample_workspace_json
    ):
        route = mock_api.get("/workspaces/5").respond(200, json=sample_workspace_json)
        sdk.workspaces.get(5, timeout=3.5)
        assert route.calls.last.request.extensions["timeout"]["read"] == 3.5

    def test_input_dto_is_shared_with_async_flavor(
        self, sdk, mock_api, sample_workspace_json
    ):
        """A payload built from the async package must work on the sync client."""
        assert WorkspaceCreate is codesphere.WorkspaceCreate
        route = mock_api.post("/workspaces").respond(201, json=sample_workspace_json)

        payload = codesphere.WorkspaceCreate(team_id=1, name="ws", plan_id=8)
        sdk.workspaces.create(payload)

        sent = json.loads(route.calls.last.request.content)
        assert sent == {
            "teamId": 1,
            "name": "ws",
            "planId": 8,
            "isPrivateRepo": True,
            "replicas": 1,
        }


class TestFlagGating:
    def test_flags_cached_via_threading_lock(self, sdk, mock_api):
        route = mock_api.get("/ide-service/flags").respond(
            200,
            json={
                "internal": {"available": [], "enabled": []},
                "preview": {"available": [], "enabled": []},
                "features": {"available": ["msd"], "enabled": []},
            },
        )

        assert sdk.flags.is_available("msd") is True
        assert sdk.flags.is_enabled("msd") is False
        assert route.call_count == 1  # cached after first fetch

        with pytest.raises(FeatureNotEnabledError):
            sdk.flags.require("msd")

    def test_legacy_platform_404_yields_empty_snapshot(self, sdk, mock_api):
        route = mock_api.get("/ide-service/flags").respond(404, json={})
        snapshot = sdk.flags.get()
        again = sdk.flags.get()
        assert snapshot.is_available("anything") is False
        assert again == snapshot
        assert route.call_count == 1
