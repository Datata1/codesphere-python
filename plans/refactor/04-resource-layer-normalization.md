# 04 — One module layout, one execution idiom, shared scoped-resource bases

**Priority:** P2
**Depends on:** 02

## Problem

The resource packages never settled on a single pattern, so a contributor has no canonical
template to copy:

- **File naming chaos.** The manager class lives in `manager.py` for `team/domain` and
  `team/usage`, but in `models.py` for `workspace/envVars`, `workspace/git`,
  `workspace/landscape`, `workspace/logs`. `git` uses `schema.py` (singular) while everything
  else uses `schemas.py`. The `envVars/` directory is camelCase in a snake_case tree.
  `workspace/landscape/resources.py` is a zero-byte file; `resources/__init__.py` is empty.
- **Two contradictory execution idioms** (pre-ticket-02): Field-wired ops vs direct
  `self._execute_operation(_OP, ...)` calls. Ticket 02 standardizes the mechanism; this ticket
  sweeps the remaining structural drift.
- **Copy-pasted scoped-manager boilerplate.** Six managers repeat the same
  `__init__(self, http_client, workspace_id/team_id)` (e.g. `envVars/models.py`,
  `git/models.py`, `landscape/models.py`, `logs/models.py`, `domain/manager.py`,
  `usage/manager.py`).
- **Domain ops defined twice.** `team/domain/operations.py` sets `response_model=DomainBase`,
  then `team/domain/manager.py:20-53` overrides every single op via
  `model_copy(update={"response_model": Domain})`. `Domain.verify_status` is annotated
  `AsyncCallable[None]` while its op returns `DomainVerificationStatus`.
- **Convention breaks & duplication.** `EnvVar` (`envVars/schemas.py`) uses plain `BaseModel`
  instead of `CamelModel` (loses aliasing and the `to_dict/to_json/to_yaml` helpers).
  `PipelineStatusList` (`landscape/schemas.py:41`) reimplements exactly what
  `core.base.ResourceList` provides. The `min(max(1, x), 100)` clamp appears 4× in
  `team/usage/manager.py:72,91,128,151`. `UsageSummaryResponse.refresh` and
  `UsageEventsResponse.refresh` are near-identical. `utils.dict_to_model_list` has zero callers
  and a `key_field: str = None` typing bug.

## Approach

1. **Canonical per-resource layout** (document in CONTRIBUTING.md alongside ticket 02's
   recipe): each resource package contains exactly `operations.py` (op constants),
   `schemas.py` (pydantic models), `resources.py` (`ResourceBase` subclasses), `__init__.py`
   (re-exports). Rename `manager.py`/`models.py`/`schema.py` accordingly; delete the
   zero-byte `landscape/resources.py` placeholder content merge.

2. **Rename `envVars/` → `env_vars/`**, keeping the public import surface stable: the
   re-exports in `workspace/__init__.py` (`from .env_vars import EnvVar, ...`) keep the paths
   users actually import (`codesphere.resources.workspace.envVars` deep imports appear in
   examples — keep a thin `envVars.py` shim module emitting `DeprecationWarning`, or update
   the examples and CHANGELOG if a clean break is preferred; decide at implementation time,
   shim recommended since the SDK is published).

3. **Scoped bases in `core/base.py`:**
   ```python
   class TeamScopedResource(ResourceBase):
       def __init__(self, http_client: APIHttpClient, team_id: int) -> None: ...

   class WorkspaceScopedResource(ResourceBase):
       def __init__(self, http_client: APIHttpClient, workspace_id: int) -> None: ...
   ```
   All six scoped managers subclass these; the copy-pasted `__init__`s are deleted.

4. **Domain ops defined once** with their final `response_model=Domain` /
   `ResourceList[Domain]` directly in `operations.py` (ticket 02's frozen dataclass makes
   `model_copy` impossible anyway). Fix `verify_status` to return
   `DomainVerificationStatus`, matching its op.

5. **Convention/duplication sweep:**
   - `EnvVar(CamelModel)`.
   - Delete `PipelineStatusList`; use `ResourceList[PipelineStatus]` (re-export the old name
     as an alias for compatibility).
   - One clamp: `PageSize = Annotated[int, Field(ge=1, le=100)]` on the request models, or a
     single `_clamp_page_size()` helper in `team/usage`.
   - Hoist the shared `refresh()` onto `PaginatedResponse`; while there, make
     `limit`/`offset` non-Optional with defaults (removes the repeated `self.limit or 25`
     re-defaulting).
   - Delete `utils.dict_to_model_list` (dead code); if `utils.py` becomes empty, delete it.

## Breaking changes

- Internal module paths move (`...domain.manager` → `...domain.resources`, etc.). Public
  re-exports from `codesphere` and the package `__init__.py`s stay stable; the `envVars` deep
  path gets a deprecation shim (recommended) per step 2.

## Acceptance criteria

- [ ] `find src -name "manager.py" -o -name "models.py" -o -name "schema.py"` returns nothing;
      no zero-byte modules; no camelCase directories (modulo the optional shim module).
- [ ] `grep -rn "model_copy(update" src/codesphere/resources` is empty.
- [ ] At most one page-size clamp implementation; one `refresh()` implementation.
- [ ] `EnvVar` round-trips camelCase aliases like every other schema (test).
- [ ] Examples still run (`examples/sdk_demo.py` imports resolve).
- [ ] Touched paths removed from the ty ratchet; `uv run ty check` passes.
