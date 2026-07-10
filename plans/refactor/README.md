# Refactor Tickets

Outcome of a full codebase review (2026-07-10) focused on **strong typing** and **easy extensibility**.

The SDK's layered design (declarative `APIOperation` constants + thin resource facades + pydantic
response validation) is a solid, extensible spine. The findings concentrate on two gaps:

1. **The typing story is aspirational, not enforced.** The package ships `py.typed` and the
   contribution docs demand strict type hints, but no type checker runs anywhere — and the core
   dispatch mechanism (`__getattribute__` interception of `Field`-wrapped operations) could not
   pass one as written.
2. **The declared contracts aren't what the runtime does.** `input_model` is never validated,
   `CS_BASE_URL` is dead, `import codesphere` crashes without `CS_TOKEN`, and empty request
   bodies are silently dropped.

## Tickets

| # | Ticket | Priority | Depends on |
|---|--------|----------|------------|
| 01 | [Typing gate (ty) & tooling cleanup](01-typing-gate-and-tooling.md) | P1 | — |
| 02 | [Typed operation dispatch](02-typed-operation-dispatch.md) | P1 (keystone) | 01 |
| 03 | [Client config & lifecycle](03-client-config-lifecycle.md) | P1 | 01 (partially parallel to 02) |
| 04 | [Resource layer normalization](04-resource-layer-normalization.md) | P2 | 02 |
| 05 | [Logs & landscape hardening](05-logs-landscape-hardening.md) | P2 | 02 |
| 06 | [Test suite at the HTTP boundary](06-test-suite-http-boundary.md) | P2 | 02, 03 |
| 07 | [Opt-in retry support](07-retry-support.md) | P3 | 03, 06 |

## Sequencing rationale

- **01 lands first** and turns the `ty` gate on immediately as a *ratchet*: known-broken paths
  (`core/`, `resources/`, `http_client.py`, `client.py`) are excluded at first, so the gate is
  blocking for everything else (and all new code) from day one without waiting on the dispatch
  rewrite.
- **02 is the keystone** — every later ticket builds on the explicit `_execute` dispatch it
  introduces. Each ticket's acceptance criteria include removing its own paths from the ty
  ratchet, so type-checked coverage only ever grows.
- **03** can start in parallel with 02 (different files), with one small ordering note on the
  duplicate-serialization removal (see ticket).
- **Public API stability:** across all tickets, only symbols exported from the top-level
  `codesphere` package (plus documented deep imports like `codesphere.resources.workspace.*`
  re-exports) are treated as public. `codesphere.core` internals may change freely; ticket 02
  formalizes this.
