# 05 — Deduplicate the logs stream/collect trio; make profile writes injection-safe

**Priority:** P2
**Depends on:** 02

## Problem

1. **The stream/collect API is the same code six times.** `workspace/logs/models.py` defines
   `stream` / `stream_server` / `stream_replica` (lines ~205-237) and `collect` /
   `collect_server` / `collect_replica` (~238-293). Each trio differs only in which
   `StreamOperation` it selects and which id kwarg it passes; each `collect_*` is an identical
   `async with ... as stream: async for ...` accumulation wrapper around its `stream_*`. Any
   fix or feature (filters, timeouts) must be applied six times.

2. **`save_profile` builds a shell heredoc from user content.**
   `workspace/landscape/models.py:87`:
   ```python
   f"cat > {filename} << 'PROFILE_EOF'\n{body}PROFILE_EOF\n"
   ```
   executed remotely via `execute_command`. The profile *name* is regex-validated, but the
   YAML *body* is interpolated raw: content containing a line `PROFILE_EOF` truncates the file
   and executes the remainder as shell; CRLF/backslash edge cases corrupt content.
   `delete_profile` (`models.py:95`) does `rm -f {filename}` — safe only because of the name
   regex, worth an assertion. This is also a design smell (remote file management expressed as
   string-built shell), but the injection fix is the actionable part.

3. Minor: `LogStream` hardcodes `httpx.Timeout(5.0, read=None)` and SSE terminator event names
   (`"end", "close", "done", "complete"`), and reaches into the private
   `self._http_client._get_client()`.

## Approach

1. **One parametrized stream path.** Introduce frozen target dataclasses, each knowing its
   `StreamOperation` and path params:
   ```python
   @dataclass(frozen=True, slots=True)
   class StageTarget:   stage: LogStage; step: int = 0
   @dataclass(frozen=True, slots=True)
   class ServerTarget:  step: int; server: str
   @dataclass(frozen=True, slots=True)
   class ReplicaTarget: step: int; replica: str

   LogTarget = StageTarget | ServerTarget | ReplicaTarget

   class WorkspaceLogsResource(WorkspaceScopedResource):
       def stream(self, target: LogTarget, ...) -> LogStream: ...
       async def collect(self, target: LogTarget, ...) -> list[LogEntry]:  # implemented on stream()
   ```
   Keep the six existing method names as one-line deprecated shims delegating to
   `stream(...)`/`collect(...)` (emit `DeprecationWarning`), since the SDK is published.

2. **Base64 transport for profile content.** Replace the heredoc with content-independent
   plumbing:
   ```python
   f"printf '%s' '{b64}' | base64 -d > '{filename}'"
   ```
   where `b64 = base64.b64encode(body.encode()).decode()` (alphabet is `[A-Za-z0-9+/=]`, inert
   in single quotes) and `filename` remains regex-validated (`ci.<name>.yml`). Add an
   adversarial round-trip unit test: content containing `PROFILE_EOF`, single/double quotes,
   `$(reboot)`, backticks, CRLF, and unicode must be written byte-identically (assert on the
   command string in unit tests; optionally cover in integration).

3. While in the file: take the SSE read timeout from the client's configured timeouts instead
   of the hardcoded `Timeout(5.0, read=None)`; name the terminator event set as a module-level
   constant; expose whatever accessor `LogStream` needs on `APIHttpClient` instead of calling
   `_get_client()` from outside.

4. Tighten `LogEntry` typing: `kind` becomes a `str`-based `Enum` (`"I"`/`"E"`, with a
   fallback for unknown values) instead of `Optional[str]` on an `extra="allow"` model.

## Breaking changes

None — old method names remain as deprecated shims; profile files are byte-identical after the
transport change.

## Acceptance criteria

- [ ] Stream/collect logic exists once; the six legacy names are 1-line shims with
      `DeprecationWarning` (tested via `pytest.warns`).
- [ ] Adversarial-content profile test passes (including a literal `PROFILE_EOF` line and
      `$(...)`).
- [ ] No heredoc construction remains: `grep -rn "PROFILE_EOF" src/` is empty.
- [ ] `workspace/logs/**` and `workspace/landscape/**` removed from the ty ratchet;
      `uv run ty check` passes.
