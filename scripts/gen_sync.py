"""Generate the sync client tree (src/codesphere/_sync) from the async source.

Runs unasyncd (configured in pyproject.toml), restores ``__all__`` blocks
that unasyncd empties in re-export-only modules (class names are identical
in both trees, so the async block is copied verbatim), then normalizes the
result with the project's ruff config.

Usage: uv run python scripts/gen_sync.py
CI freshness check: run this script, then `git diff --exit-code src/codesphere/_sync`.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASYNC_DIR = ROOT / "src/codesphere/_async"
SYNC_DIR = ROOT / "src/codesphere/_sync"

_ALL_RE = re.compile(r"^__all__ = \[[^\]]*\]", re.MULTILINE | re.DOTALL)


def run(*cmd: str, fatal: bool = True) -> None:
    result = subprocess.run(cmd, cwd=ROOT)
    if fatal and result.returncode != 0:
        sys.exit(result.returncode)


def restore_all_blocks() -> int:
    restored = 0
    for src in ASYNC_DIR.rglob("*.py"):
        source_all = _ALL_RE.search(src.read_text())
        if source_all is None:
            continue
        target = SYNC_DIR / src.relative_to(ASYNC_DIR)
        if not target.exists():
            continue
        text = target.read_text()
        target_all = _ALL_RE.search(text)
        if target_all is None or target_all.group(0) == source_all.group(0):
            continue
        target.write_text(
            text[: target_all.start()] + source_all.group(0) + text[target_all.end() :]
        )
        restored += 1
    return restored


def main() -> None:
    run("uv", "run", "unasyncd")
    restored = restore_all_blocks()
    print(f"Restored __all__ in {restored} generated files")
    # Remaining findings are silenced via per-file-ignores in ruff.toml;
    # fix what is fixable but do not fail generation on the rest.
    run("uv", "run", "ruff", "check", "--fix", "--quiet", str(SYNC_DIR), fatal=False)
    run("uv", "run", "ruff", "format", "--quiet", str(SYNC_DIR))


if __name__ == "__main__":
    main()
