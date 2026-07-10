# 01 — Add a blocking `ty` type-check gate (ratcheted) and clean up tooling config

**Priority:** P1
**Depends on:** —
**Unblocks:** 02–07 (the ratchet is how later tickets prove their typing work)

## Problem

The SDK ships `src/codesphere/py.typed` (so downstream type checkers trust our annotations) and
`.github/copilot-instructions.md` states "Strict type hints required" — but **no type checker
exists anywhere**: not in dev dependencies, not in `.pre-commit-config.yaml`, not in
`.github/workflows/ci.yml`. The claim is unenforced, and several annotations in `core/` are
actively wrong (see ticket 02).

Surrounding tooling config has drifted:

- `ruff.toml` selects only `["F", "E4", "E7", "E9"]` and ignores `E721`/`F841` (unused locals
  pass lint). Its `exclude` list references `src/codesphere_sdk/...` paths that don't exist —
  leftovers from a generated-client era.
- `pyproject.toml` `[tool.coverage.run]` has `source = ["api", "handler", "tasks"]`
  (pyproject.toml:64) — none of those packages exist, so coverage numbers are unanchored.
  `omit` also lists nonexistent `docs/*` / `scripts/**` roots.
- `pyproject.toml:13-14,22` declare `aiohttp`, `aiohttp-retry`, and `urllib3` as runtime
  dependencies; `grep -r` over `src/` shows zero imports of any of them (the SDK is pure httpx).
  They bloat installs and imply a retry feature that doesn't exist (see ticket 07).
- `requires-python = ">=3.12.9"` (pyproject.toml:11) pins an oddly specific patch release,
  excluding 3.12.0–3.12.8 users for no identified reason.

## Approach

Toolchain choice: **`ty`** (Astral) rather than mypy/pyright, to keep type checking and linting
in the same toolchain family as ruff. ty is pre-1.0: **pin its version** in the dev group and
expect occasional rule renames on upgrades (note this in a comment next to the pin).

1. **Add ty as a blocking gate with a ratchet.**
   - `uv add --dev ty` (pinned, e.g. `ty==0.0.x`).
   - Configure in `pyproject.toml` under `[tool.ty]`: `src.root = "src"`, error-level rules for
     the strictness-relevant checks (unresolved attributes, invalid assignments, invalid
     argument types, missing/implicit `Any` where ty supports it).
   - **Ratchet:** exclude the paths that cannot pass until later tickets land, via
     `[[tool.ty.overrides]]` (or `src.exclude` if the pinned ty version's override granularity
     is insufficient):
     - `src/codesphere/core/**` and `src/codesphere/resources/**` → removed by tickets 02/04
     - `src/codesphere/http_client.py`, `src/codesphere/client.py`, `src/codesphere/config.py` → removed by ticket 03
     Annotate each exclusion with the ticket number that deletes it.
   - CI: add a `typecheck` job to `.github/workflows/ci.yml` running `uv run ty check`
     (blocking). Add the same to `.pre-commit-config.yaml` and a `make typecheck` target.

2. **Broaden ruff.**
   - `select = ["F", "E", "W", "I", "UP", "B", "SIM", "RUF"]`; drop the `F841` and `E721`
     ignores; delete the entire stale `src/codesphere_sdk/*` exclude block.
   - Run `ruff check --fix` + `ruff format`; fix the residue by hand (expect mostly import
     sorting and pyupgrade rewrites like `Optional[X]` → `X | None`).

3. **Fix coverage config.** `[tool.coverage.run] source = ["src/codesphere"]`; prune the
   nonexistent `omit` entries; change the CI pytest invocation from `--cov=.` to rely on the
   config (`--cov`).

4. **Prune dependencies.** Remove `aiohttp`, `aiohttp-retry`, `urllib3` from
   `[project.dependencies]`. While there, grep-verify each remaining runtime dep is actually
   imported (`python-dateutil` is suspect) and remove any that aren't. `uv lock` after.

5. **Relax the Python floor** to `requires-python = ">=3.12"` (align `.python-version` and
   `ruff.toml target-version = "py312"`, which already agree).

## Breaking changes

None. Dependency removals only shrink the install footprint; relaxing `requires-python` widens
compatibility.

## Acceptance criteria

- [ ] CI fails on any ty error outside the documented ratchet exclusions; `make typecheck` and
      the pre-commit hook run the same command.
- [ ] Every ratchet exclusion carries a comment naming the ticket that removes it.
- [ ] `ruff check` passes with the broadened rule set; no `codesphere_sdk` references remain in
      `ruff.toml`.
- [ ] Coverage output reports lines in `src/codesphere/**` (spot-check the CI coverage comment).
- [ ] Fresh `uv pip install .` pulls neither aiohttp nor urllib3; `uv.lock` regenerated.
- [ ] `requires-python = ">=3.12"`.
