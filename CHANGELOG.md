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

### Changed

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
