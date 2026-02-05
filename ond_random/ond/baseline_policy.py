from __future__ import annotations

import json
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Tuple


def load_policy(path: str) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "default" not in data:
        raise ValueError("Baseline policy must include a 'default' section")
    return data


def _policy_match(entry: Dict[str, Any], protocol: str, scheme: str) -> bool:
    p = entry.get("protocol", "*")
    s = entry.get("scheme", "*")
    return fnmatch(protocol, p) and fnmatch(scheme, s)


def select_policy(data: Dict[str, Any], protocol: str, scheme: str) -> Tuple[Tuple[float, float, float], str]:
    domains = data.get("domains", [])
    for entry in domains:
        if _policy_match(entry, protocol, scheme):
            percentiles = entry.get("percentiles")
            profile = entry.get("profile")
            if percentiles and len(percentiles) == 3:
                return (float(percentiles[0]), float(percentiles[1]), float(percentiles[2])), str(profile or data["default"].get("profile", "core"))
    default = data["default"]
    pct = default.get("percentiles", [50, 80, 95])
    profile = default.get("profile", "core")
    return (float(pct[0]), float(pct[1]), float(pct[2])), str(profile)

