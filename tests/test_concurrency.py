"""Concurrency regression tests for the async client.

Each test encodes an invariant that one SDK instance shared across tasks must
uphold. Interleaving is driven by ``asyncio.Event`` handshakes rather than
wall-clock sleeps, so the ordering under test is deterministic and these do
not flake on a loaded machine.

Tests assert the *invariant*, not the mechanism: they check that a failure
surfaces as a ``CodesphereError``, not that a particular exception class was
raised. That keeps them honest about what callers actually depend on.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from codesphere import CodesphereSDK, NotFoundError, RetryConfig
from codesphere.exceptions import CodesphereError
from codesphere.feature_flags import FLAGS_ENDPOINT

BASE = "https://concurrency.test/api"


@pytest.fixture
def api():
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def sdk():
    return CodesphereSDK(token="t", base_url=BASE, retry=RetryConfig(max_retries=0))


@pytest.fixture
def sleep_mock():
    """Collapse retry backoff so retry tests stay fast."""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock:
        yield mock


class TestClientLifecycle:
    async def test_concurrent_scopes_do_not_close_each_other(self, api, sdk):
        """Two tasks sharing one SDK: the first to exit must not tear down
        the transport out from under the second."""
        api.get("/teams").respond(200, json=[])

        first_exited = asyncio.Event()
        second_entered = asyncio.Event()

        async def first():
            async with sdk:
                # Hold the scope open until the second one is inside it too,
                # so the two genuinely overlap.
                await second_entered.wait()
            first_exited.set()

        async def second():
            async with sdk:
                second_entered.set()
                await first_exited.wait()
                # The other scope is gone; ours is still open.
                return await sdk.teams.list()

        _, teams = await asyncio.gather(first(), second())
        assert teams == []

    async def test_nested_scope_stays_open_until_outermost_exit(self, api, sdk):
        api.get("/teams").respond(200, json=[])

        async with sdk:
            async with sdk:
                await sdk.teams.list()
            # Inner scope exited; the outer scope still owns an open client.
            assert await sdk.teams.list() == []

    async def test_transport_is_closed_once_every_scope_exits(self, api, sdk):
        api.get("/teams").respond(200, json=[])

        # Nesting is the point of this test, so it is not collapsible.
        async with sdk:  # noqa: SIM117
            async with sdk:
                pass
        assert sdk._http_client._client is None

    async def test_request_without_open_raises_sdk_error(self, api, sdk):
        api.get("/teams").respond(200, json=[])

        with pytest.raises(CodesphereError) as exc_info:
            await sdk.teams.list()
        # Kept as a RuntimeError too, so existing handlers keep working.
        assert isinstance(exc_info.value, RuntimeError)

    async def test_close_during_retry_backoff_raises_sdk_error(self, api):
        """Closing mid-backoff must not leak httpx's own RuntimeError."""
        api.get("/teams").respond(503, json={})
        sdk = CodesphereSDK(
            token="t",
            base_url=BASE,
            retry=RetryConfig(max_retries=3, backoff_factor=0.3),
        )
        await sdk.open()

        task = asyncio.create_task(sdk.teams.list())
        await asyncio.sleep(0.05)  # let the first attempt fail into backoff
        await sdk.close()

        with pytest.raises(CodesphereError):
            await task


class TestFlagsCache:
    @staticmethod
    def _snapshot() -> dict:
        return {"features": {"available": ["gadgets"], "enabled": ["gadgets"]}}

    async def test_invalidate_during_inflight_fetch_is_not_lost(self, api, sdk):
        """A fetch that started before invalidate() must not repopulate the
        cache it was told to drop."""
        fetch_started = asyncio.Event()
        release = asyncio.Event()
        calls = 0

        async def flags(request):
            nonlocal calls
            calls += 1
            fetch_started.set()
            await release.wait()
            return httpx.Response(200, json=self._snapshot())

        api.get(FLAGS_ENDPOINT).mock(side_effect=flags)

        async with sdk:
            store = sdk._http_client.flags_store
            task = asyncio.create_task(sdk.flags.get())
            await fetch_started.wait()

            store.invalidate()
            release.set()
            await task

            assert store.cached() is None, "invalidate() was silently discarded"
            await sdk.flags.get()
            assert calls == 2, "the invalidated snapshot was served from cache"

    async def test_concurrent_first_reads_fetch_once(self, api, sdk):
        """Regression guard: the lock already dedupes: keep it that way."""
        route = api.get(FLAGS_ENDPOINT).respond(200, json=self._snapshot())

        async with sdk:
            await asyncio.gather(*(sdk.flags.get() for _ in range(8)))

        assert route.call_count == 1


class TestRetrySideEffects:
    async def test_retried_delete_404_is_treated_as_success(
        self, api, sleep_mock, sample_workspace_data
    ):
        """The first DELETE reached the server behind a 503; the retry then
        sees 404. The resource is gone, which is what the caller asked for."""
        api.get("/workspaces/72678").respond(200, json=sample_workspace_data)
        route = api.delete("/workspaces/72678/landscape/teardown")
        route.side_effect = [
            httpx.Response(503),
            httpx.Response(404, json={"message": "no landscape deployed"}),
        ]

        sdk = CodesphereSDK(token="t", base_url=BASE, retry=RetryConfig(max_retries=2))
        async with sdk:
            workspace = await sdk.workspaces.get(72678)
            await workspace.landscape.teardown()

        assert route.call_count == 2

    async def test_first_attempt_404_still_raises(
        self, api, sleep_mock, sample_workspace_data
    ):
        api.get("/workspaces/72678").respond(200, json=sample_workspace_data)
        api.delete("/workspaces/72678/landscape/teardown").respond(
            404, json={"message": "no landscape deployed"}
        )

        sdk = CodesphereSDK(token="t", base_url=BASE, retry=RetryConfig(max_retries=2))
        async with sdk:
            workspace = await sdk.workspaces.get(72678)
            with pytest.raises(NotFoundError):
                await workspace.landscape.teardown()

    async def test_retried_non_delete_404_still_raises(self, api, sleep_mock):
        """The 404-as-success rule is scoped to DELETE. A PUT that 404s
        after a retry is a genuine miss, not a completed write."""
        route = api.put("/workspaces/72678/env-vars")
        route.side_effect = [
            httpx.Response(503),
            httpx.Response(404, json={"message": "no such workspace"}),
        ]

        sdk = CodesphereSDK(token="t", base_url=BASE, retry=RetryConfig(max_retries=2))
        async with sdk:
            with pytest.raises(NotFoundError):
                await sdk._http_client.request("PUT", "/workspaces/72678/env-vars")

        assert route.call_count == 2


class TestModelStaleness:
    async def test_concurrent_updates_never_leave_a_lying_model(
        self, api, sdk, sample_workspace_data
    ):
        """The server orders writes by arrival, the client by response
        latency. When those disagree, the local model must refuse to answer
        rather than report a value the platform does not hold.
        """
        from codesphere.models.workspace import WorkspaceUpdate

        api.get("/workspaces/72678").respond(200, json=sample_workspace_data)

        applied: list[str] = []
        second_applied = asyncio.Event()

        async def patch_workspace(request):
            name = json.loads(request.content)["name"]
            if name == "second":
                # "second" reaches the server last, so the server ends on it.
                await asyncio.sleep(0)
                applied.append(name)
                second_applied.set()
                return httpx.Response(200)
            applied.append(name)
            # ...but its response comes back first, so a naive write-back
            # would leave the model claiming "first".
            await second_applied.wait()
            return httpx.Response(200)

        api.patch("/workspaces/72678").mock(side_effect=patch_workspace)

        async with sdk:
            workspace = await sdk.workspaces.get(72678)
            await asyncio.gather(
                workspace.update(WorkspaceUpdate(name="first")),
                workspace.update(WorkspaceUpdate(name="second")),
            )

            server_value = applied[-1]
            try:
                local_value = workspace.name
            except CodesphereError:
                return  # refused to answer: correct
            assert local_value == server_value, (
                f"model reports {local_value!r} but the server holds "
                f"{server_value!r} (apply order: {applied})"
            )
