"""Concurrency regression tests for the generated sync client.

The sync twin runs under real threads, so check-then-act patterns that are
invisible in asyncio (no await between the check and the assignment) become
genuine data races here. ``threading.Barrier`` widens the window
deterministically instead of relying on scheduling luck.
"""

import threading
import time

import httpx
import pytest
import respx

from codesphere import RetryConfig
from codesphere.exceptions import CodesphereError
from codesphere.feature_flags import FLAGS_ENDPOINT
from codesphere.sync import CodesphereSDK

BASE = "https://sync-concurrency.test/api"

FLAGS_JSON = {"features": {"available": ["gadgets"], "enabled": ["gadgets"]}}


@pytest.fixture
def api():
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def sdk():
    return CodesphereSDK(token="t", base_url=BASE, retry=RetryConfig(max_retries=0))


def _run_in_threads(target, count: int) -> list[BaseException]:
    errors: list[BaseException] = []

    def wrapper():
        try:
            target()
        except BaseException as exc:  # the assertion below surfaces it
            errors.append(exc)

    threads = [threading.Thread(target=wrapper) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)
    return errors


class TestClientLifecycle:
    def test_concurrent_open_builds_exactly_one_transport(self, api, sdk):
        """Two threads racing open() must not each construct (and leak) a
        connection pool."""
        constructed: list[httpx.Client] = []
        real_init = httpx.Client.__init__
        # Rendezvous before open(), so both threads enter it together. The
        # barrier must not live inside the construction path: once the race
        # is fixed only one thread constructs, and a barrier there would
        # deadlock on the correct behavior.
        start = threading.Barrier(2, timeout=5)

        def spy_init(self, *args, **kwargs):
            constructed.append(self)
            time.sleep(0.05)  # hold the check-then-act window open
            return real_init(self, *args, **kwargs)

        def open_together():
            start.wait()
            sdk.open()

        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(httpx.Client, "__init__", spy_init)
            errors = _run_in_threads(open_together, 2)

        try:
            assert not errors, f"open() raised under contention: {errors}"
            orphans = [c for c in constructed if c is not sdk._http_client._client]
            assert len(constructed) == 1, (
                f"{len(constructed)} transports constructed, "
                f"{len(orphans)} orphaned and never closed"
            )
        finally:
            # Both threads entered a scope; balance both.
            sdk.close()
            sdk.close()

    def test_concurrent_scopes_do_not_close_each_other(self, api, sdk):
        api.get("/teams").respond(200, json=[])

        second_entered = threading.Event()
        first_exited = threading.Event()
        errors: list[BaseException] = []

        def first():
            try:
                with sdk:
                    second_entered.wait(timeout=5)
            except BaseException as exc:  # surfaced in the assertion below
                errors.append(exc)
            first_exited.set()

        def second():
            try:
                with sdk:
                    second_entered.set()
                    first_exited.wait(timeout=5)
                    # The other scope is gone; ours is still open.
                    sdk.teams.list()
            except BaseException as exc:  # surfaced in the assertion below
                errors.append(exc)

        threads = [threading.Thread(target=first), threading.Thread(target=second)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        assert not errors, f"a scope was torn down early: {errors}"

    def test_request_without_open_raises_sdk_error(self, api, sdk):
        api.get("/teams").respond(200, json=[])

        with pytest.raises(CodesphereError) as exc_info:
            sdk.teams.list()
        assert isinstance(exc_info.value, RuntimeError)


class TestFlagsCache:
    def test_concurrent_first_reads_fetch_once(self, api, sdk):
        route = api.get(FLAGS_ENDPOINT).respond(200, json=FLAGS_JSON)

        with sdk:
            errors = _run_in_threads(sdk.flags.get, 8)

        assert not errors
        assert route.call_count == 1

    def test_invalidate_during_inflight_fetch_is_not_lost(self, api, sdk):
        fetch_started = threading.Event()
        release = threading.Event()
        calls = 0

        def flags(request):
            nonlocal calls
            calls += 1
            fetch_started.set()
            release.wait(timeout=5)
            return httpx.Response(200, json=FLAGS_JSON)

        api.get(FLAGS_ENDPOINT).mock(side_effect=flags)

        with sdk:
            store = sdk._http_client.flags_store
            worker = threading.Thread(target=sdk.flags.get)
            worker.start()
            fetch_started.wait(timeout=5)

            store.invalidate()
            release.set()
            worker.join(timeout=5)

            assert store.cached() is None, "invalidate() was silently discarded"
            sdk.flags.get()
            assert calls == 2, "the invalidated snapshot was served from cache"
