# 02 — Replace `__getattribute__` operation magic with an explicit, fully-typed `_execute`

**Priority:** P1 — keystone ticket
**Depends on:** 01 (ty ratchet in place)
**Unblocks:** 04, 05, 06

## Problem

The operation dispatch layer is invisible to type checkers and its declared types are wrong in
four independent ways:

1. **The `AsyncCallable` alias lies about its signature.**
   `src/codesphere/core/operations.py:10`:
   ```python
   AsyncCallable: TypeAlias = Callable[[], Awaitable[_T]]
   ```
   declares **zero parameters**, but every call site passes kwargs —
   `self.get_team_op(team_id=team_id)` (`resources/team/resources.py:28`),
   `self.create_team_op(data=payload)` (`:33`), and the same in every other resource. Under any
   type checker each operation call is a "too many arguments" error.

2. **The wiring is runtime magic no checker can follow.** Resources declare ops as
   `op: AsyncCallable[T] = Field(default=_OP, exclude=True)` on classes that are **not**
   pydantic models (`ResourceBase` in `core/base.py:13` is a plain class), so `Field(...)` is
   just a `FieldInfo` in a class attribute and `exclude=True` is meaningless.
   `_APIOperationExecutor.__getattribute__` (`core/handler.py:18-31`) then sniffs **every**
   attribute access for `FieldInfo`/`APIOperation` and swaps in
   `partial(self._execute_operation, operation=op)`. The static type (`AsyncCallable`), the
   assigned value (`FieldInfo`), and the runtime value (a partial) are three different things.

3. **The executor spine is `Any` end to end.** `_execute_operation` (`handler.py:33`),
   `execute` (`:54`), and `_parse_and_validate_response` (`:106`) all return `Any`;
   `APIOperation.response_model: Type[ResponseT]` (`operations.py:18`) can't hold `type(None)`
   under strict checking; **`input_model` (`operations.py:19`) is declared on every operation
   but never read by the handler** — request payloads are never validated; and the
   `get_origin(response_model) is list` branch (`handler.py:123-124`) is dead because real list
   responses are `ResourceList[...]` RootModels (`get_origin` returns `ResourceList`, not
   `list`).

4. **Endpoint formatting scrapes hidden state and has a payload bug.**
   `_prepare_request_args` (`handler.py:65-75`) pours `self.executor.__dict__` and a full
   `model_dump()` into the format namespace (duplicating `format_args.update(self.kwargs)` at
   lines 67 and 73), so which value fills `{workspace_id}` is not grep-able. And
   `if json_data_obj := self.kwargs.get("data")` (`handler.py:78`) drops **falsy** payloads: an
   empty-dict body is silently not sent.

Related idiom smell fixed by the same rewrite: entity models mix pydantic and executor and use
a doubled annotation+assignment (`team/schemas.py:31-32`):
```python
delete: AsyncCallable[None]
delete = Field(default=APIOperation(...), exclude=True)
```

## Approach

**Chosen design: explicit generic `_execute` (delete the attribute magic).** A descriptor-based
alternative (`APIOperation.__get__` returning a typed callable) was considered and rejected: the
per-op parameters live in a *string* (`endpoint_template="/teams/{team_id}"`), so a descriptor
can type the return value but never the parameters without hand-writing a per-op `Protocol` —
duplicating the parameter list while keeping the magic. Meanwhile every resource **already**
wraps each op in a public `async def` with the real typed signature; that wrapper is the typed
surface. Collapsing to one layer is mostly deletion, and half the codebase
(`Workspace.update/delete`, `WorkspaceLandscapeManager`, …) already calls
`self._execute_operation(_OP, ...)` directly.

### New `core/operations.py`

```python
from dataclasses import dataclass
from typing import Generic, TypeVar
from pydantic import BaseModel

ResponseT = TypeVar("ResponseT")
EntryT = TypeVar("EntryT", bound=BaseModel)

@dataclass(frozen=True, slots=True)
class APIOperation(Generic[ResponseT]):
    method: str
    endpoint_template: str
    response_model: type[ResponseT]
    input_model: type[BaseModel] | None = None   # now enforced by the executor

@dataclass(frozen=True, slots=True)
class StreamOperation(Generic[EntryT]):
    endpoint_template: str
    entry_model: type[EntryT]
```

Typing facts that make this strict-clean: pydantic parametrized generics
(`ResourceList[Team]`) are real runtime classes, so `response_model=ResourceList[Team]` infers
`APIOperation[ResourceList[Team]]`; `types.NoneType` is `type[None]`, so delete/void ops are
`APIOperation[None]` and `_execute` returns `None`. Dropping `BaseModel` as the op container
removes `arbitrary_types_allowed` and the `model_copy(update={"response_model": ...})` trick in
`team/domain/manager.py:20-53` (ticket 04 deletes those call sites; use `dataclasses.replace`
if one genuinely remains). Standardize the "no response" encoding on `NoneType` — retire the
`None`-vs-`type(None)` dual sentinel.

### New `core/handler.py` — one free function

```python
async def execute_operation(
    client: APIHttpClient,
    op: APIOperation[ResponseT],
    *,
    data: BaseModel | Mapping[str, Any] | None = None,
    params: Mapping[str, Any] | None = None,
    path_params: Mapping[str, Any],
) -> ResponseT:
    # 1. endpoint = op.endpoint_template.format(**path_params) — explicit, no __dict__ scraping
    # 2. if op.input_model is not None and data is not None:
    #        data = op.input_model.model_validate(data)        # input_model finally enforced
    # 3. payload = data.model_dump(by_alias=True, exclude_none=True) if isinstance(data, BaseModel) else data
    #    guard with `if data is not None` — fixes the falsy empty-dict bug
    # 4. response = await client.request(op.method, endpoint, json=payload, params=params)
    # 5. return _parse_response(response, op.response_model, client)
```

`_parse_response(response, model: type[ResponseT], client) -> ResponseT` handles: `NoneType` →
return `None`; otherwise `model.model_validate(response.json())` + inject the client into
bound models / `ResourceList` items (port `_inject_client_into_model`). The dead
`get_origin(...) is list` branch is not ported. Wrap the pydantic `ValidationError` in the
SDK's own response-validation error (or re-raise deliberately and document it) so users don't
have to catch pydantic internals.

### New bases in `core/base.py`

```python
class ResourceBase:
    def __init__(self, http_client: APIHttpClient) -> None:
        self._http_client = http_client

    async def _execute(
        self, op: APIOperation[ResponseT], *,
        data: BaseModel | Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        **path_params: Any,
    ) -> ResponseT:
        return await execute_operation(self._http_client, op, data=data, params=params, path_params=path_params)


class BoundModel(CamelModel):
    """API entity that carries the HTTP client it was fetched with (Team, Workspace, Domain, …)."""
    _http_client: APIHttpClient | None = PrivateAttr(default=None)

    def _client(self) -> APIHttpClient:
        # replaces validate_http_client(); raise the "detached model" RuntimeError (or a
        # dedicated DetachedModelError) when None
        ...

    async def _execute(self, op: APIOperation[ResponseT], *, data=None, params=None, **path_params: Any) -> ResponseT:
        return await execute_operation(self._client(), op, data=data, params=params, path_params=path_params)
```

`_execute` is deliberately duplicated as a one-line delegation in each base instead of a shared
mixin — mixing a plain class into pydantic bases is what produced the current
`PrivateAttr`-on-plain-class confusion. `data`/`params` are reserved kwarg names (cannot be
path params); no current endpoint template uses either.

**Deleted:** `_APIOperationExecutor`, `APIRequestHandler`, `AsyncCallable`, the
`__getattribute__` override. `core/__init__.py` re-exports become: `ResourceBase`,
`BoundModel`, `CamelModel`, `ResourceList`, `APIOperation`, `StreamOperation`.

### A resource module after

```python
# resources/team/resources.py
class TeamsResource(ResourceBase):
    async def list(self) -> list[Team]:
        return (await self._execute(LIST_TEAMS)).root

    async def get(self, team_id: int) -> Team:
        return await self._execute(GET_TEAM, team_id=team_id)

    async def create(self, payload: TeamCreate) -> Team:
        return await self._execute(CREATE_TEAM, data=payload)

# resources/team/schemas.py — delete op moves to operations.py as DELETE_TEAM: APIOperation[None]
class Team(TeamBase, BoundModel):
    async def delete(self) -> None:
        await self._execute(DELETE_TEAM, team_id=self.id)
```

Migration is mechanical across the ~8 resource modules: delete the `Field`-wired op
attributes, keep every existing public method signature, and replace the body with one
`self._execute(...)` call. Templates that previously scraped `{id}`/`{workspace_id}` from
`self.__dict__` now receive them explicitly (`id=self.id`) — one extra kwarg, grep-able data
flow.

**Document the contributor recipe in CONTRIBUTING.md** (this ticket): a new resource is
(1) pydantic schemas in `schemas.py` (`CamelModel`, or `BoundModel` if the entity makes calls),
(2) `APIOperation` constants in `operations.py`, (3) a `ResourceBase` subclass with one typed
public method per op. No Field wiring, no dunder knowledge.

## Breaking changes

- **User-facing API: none.** Public signatures already lived on the wrapper methods and are
  unchanged; `sdk.teams.get(...)`, `team.delete()`, `workspace.env_vars...` behave identically.
- `codesphere.core` internals change/disappear. This ticket adds a line to the README/CHANGELOG
  declaring that only top-level `codesphere` exports (and the documented
  `codesphere.resources.*` re-exports) are public API.
- Behavior fix: payloads are now validated against `input_model` (previously silently
  unvalidated) and empty-dict bodies are now sent (previously dropped). Both are corrections;
  call them out in the CHANGELOG.

## Acceptance criteria

- [ ] `grep -rn "AsyncCallable\|__getattribute__\|APIRequestHandler\|_APIOperationExecutor" src/` is empty.
- [ ] `grep -rn "Field(default=" src/codesphere/resources src/codesphere/core` finds no
      operation wiring.
- [ ] `src/codesphere/core/**` and `src/codesphere/resources/**` removed from the ty ratchet;
      `uv run ty check` passes.
- [ ] New unit test: a payload violating `input_model` raises a validation error before any
      HTTP request is made.
- [ ] New regression test: an operation called with `data={}` sends `{}` as the JSON body.
- [ ] Full unit + integration suites pass; CONTRIBUTING.md contains the new-resource recipe.
