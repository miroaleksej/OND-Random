from __future__ import annotations

import os
import platform as _platform
import subprocess
from pathlib import Path
from typing import Any, Dict


def _env_commit() -> str | None:
    return os.getenv("OND_RANDOM_GIT_COMMIT") or os.getenv("GIT_COMMIT")


def git_commit(base: Path | None = None) -> str:
    env = _env_commit()
    if env:
        return env
    try:
        cmd = ["git", "rev-parse", "HEAD"]
        if base is not None:
            cmd = ["git", "-C", str(base)] + cmd[1:]
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def platform_id() -> str:
    try:
        return _platform.platform()
    except Exception:
        return "unknown"


def resolve_provenance(
    *,
    generator_id: str | None,
    profile_id: str | None,
    commit: str | None = None,
    platform: str | None = None,
    base_path: Path | None = None,
) -> Dict[str, Any]:
    return {
        "commit": commit or git_commit(base=base_path),
        "platform": platform or platform_id(),
        "generator_id": generator_id or "unknown",
        "profile_id": profile_id or "unknown",
    }
