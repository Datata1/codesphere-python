## Unreleased

### Added

- Synchronous client: `from codesphere.sync import CodesphereSDK` mirrors
  the async API with identical signatures (generated from the async
  source via unasyncd; parity is enforced in CI). Request/response
  models are shared between both flavors via the new `codesphere.models`
  package.
- Per-call timeout: every API method now accepts a keyword-only
  `timeout=` (float or `httpx.Timeout`) that overrides the client-wide
  timeout for that call only (applied per retry attempt).
- Hosted documentation site (mkdocs-material + mkdocstrings) with
  quickstart, guides, full API reference, and `llms.txt`; deployed to
  GitHub Pages on pushes to `main`.

### Added

- Concurrency guide covering what is safe to share, how stale models
  work, and the lost-update windows the Codesphere API provides no way
  to close (it has no ETags, `If-Match`, or idempotency keys).
- `Workspace.refresh()` and `Domain.refresh()` re-read an entity from the
  server in place.

### Fixed

- `wait_for_stage()` pins the pipeline run it is waiting on by its start
  time and raises `ConflictError` if someone else restarts the stage
  meanwhile, instead of silently reporting the outcome of a run the
  caller never started.
- `wait_for_stage()` and `wait_until_running()` now measure their
  `timeout` against the wall clock. Previously only the sleeps counted,
  so slow status requests could overrun the deadline substantially.
- Reusing a `LogStream` raises `ClientStateError` instead of stranding
  the first stream context or surfacing a raw `httpx.StreamConsumed`.
- Sharing one SDK across tasks or threads is now safe. `open()`/`close()`
  are reference counted, so nested and concurrent scopes no longer tear
  the transport down for each other, and two threads racing `open()` in
  the sync client can no longer each build (and orphan) a connection
  pool. Closing while a request is in flight now raises the new
  `ClientStateError` instead of leaking httpx's bare `RuntimeError`.
- `sdk.flags.invalidate()` is no longer discarded when a flags fetch is
  already in flight; the stale snapshot used to be reinstated silently.
  The `legacy_platform` marker in feature-flag errors can also no longer
  come from a different fetch than the snapshot it is reported with.
- A `404` on a retried `DELETE` is treated as success. Previously a
  teardown that had actually succeeded reported `NotFoundError` when the
  first attempt's response was lost behind a gateway error. A `404` on
  the first attempt still raises.

### Changed

- **Breaking:** writes no longer copy values back into the local model.
  `Workspace.update()`, `Domain.update()`,
  `Domain.update_workspace_connections()` and `Domain.verify_status()`
  now mark the instance **stale**: reading a field, `to_dict()`,
  `to_json()` or `to_yaml()` raises the new `StaleModelError` until you
  call `await refresh()`. The platform orders writes by arrival while the
  client sees them by response, so the old write-back could leave a model
  reporting a value the platform did not hold. Identity fields (`id`, or
  `name`/`team_id` for domains) stay readable. `Domain` methods still
  return the server's response, which is authoritative — prefer it over
  re-reading `self`.
- Retries on transient failures are now enabled by default
  (`max_retries=2`). Idempotent methods (`GET`, `HEAD`, `PUT`, `DELETE`)
  are retried on `429`/`502`/`503`/`504` and connect/timeout errors.
  Set `RetryConfig(max_retries=0)` to restore the previous opt-in
  behavior. `POST` is still never retried unless explicitly added to
  `retry_methods`.
- Debug/error logs no longer include request or response bodies (they can
  contain secrets such as env-var values); only structural information is
  logged.
- Package classifiers: `Development Status :: 5 - Production/Stable` and
  `Typing :: Typed`.

### Removed

- The deprecated module path `codesphere.resources.workspace.envVars`
  (use `codesphere.resources.workspace.env_vars`).
- `codesphere.utils.update_model_fields`, the helper behind the removed
  write-back behavior. It had no remaining callers.

## v1.0.0 (2026-02-21)

### Features

- feat(usage): Add usage history manager (#49)
- feat(pipeline-stream): add log stream (#46)
- feat(git): add git resource (#45)
- feat(landscape): add landscape resource (#41)
- feat(model-export): provide model methods to export data (#40)
- feat(exceptions): add base exceptions (#39)
- feat(agent): add copilot instructions (#35)
- feat(domain): add domains resource (#33)
- feat(workspace): implement base operations for workspaces (#32)

### Refactors

- refactor: Change README file (#37)
- refactor(filetree): reorganize files (#30)
- refactor(team): streamline api operations pattern (#29)

### Other

- release process (#51)
- demo(dashboard): add dashboard demo (#50)
- refac(commit-hook): remove commitizen (#38)
- test: fix ci
- test(suite): set up initial testsuite (#36)
- chore(test): test maintenance (#28)
- chore(types): clean types annotations (#10)

## v0.4.0 (2025-07-22)

### Feat

- **src/codesphere/resources/workspace/env-vars**: support env-vars endpoints of public api

## v0.3.0 (2025-07-22)

### Feat

- **src/resources/metadata**: implement metadata endpoints

## v0.2.3 (2025-07-21)

### Fix

- internal CI fixes

## v0.2.2 (2025-07-21)

### Fix

- **.github/workflows/ci.yml**: fix trigger

## v0.2.1 (2025-07-21)

## v0.2.0 (2025-07-16)

### Feat

- **codesphere/workspace**: add workspace resources

## v0.1.1 (2025-07-16)

### Fix

- **.github/ci.yml**: fix trigger condition

## v0.1.0 (2025-07-16)

### Feat

- **src/codesphere/team**: adding team resources from public api

## v0.0.4 (2025-07-16)

## v0.0.3 (2025-07-16)

### Fix

- **fix-repository-url-on-pypi**: fix repository url on pypi

## v0.0.2 (2025-07-16)

### Refactor

- **initial-project-setup**: initial project setup
