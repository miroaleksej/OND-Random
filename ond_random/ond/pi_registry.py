from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _empty_registry() -> Dict[str, Any]:
    return {"version": "0.1", "pi": {}}


def load_registry(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return _empty_registry()
    data = json.loads(p.read_text(encoding="utf-8"))
    if "pi" not in data or not isinstance(data["pi"], dict):
        raise ValueError("Invalid registry format: missing 'pi' map")
    return data


def save_registry(path: str, registry: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")


def find_entry(registry: Dict[str, Any], pi_id: str, pi_version: str) -> Optional[Dict[str, Any]]:
    entries = registry.get("pi", {}).get(pi_id, [])
    for entry in entries:
        if entry.get("pi_version") == pi_version:
            return entry
    return None


def add_entry(
    registry: Dict[str, Any],
    *,
    pi_id: str,
    pi_version: str,
    pi_spec_hash: str,
    obs_space: Dict[str, Any],
    description: str | None = None,
) -> Dict[str, Any]:
    if "pi" not in registry:
        registry["pi"] = {}
    entry = find_entry(registry, pi_id, pi_version)
    if entry:
        if entry.get("pi_spec_hash") != pi_spec_hash:
            raise ValueError(
                f"Registry drift for {pi_id}@{pi_version}: "
                f"{entry.get('pi_spec_hash')} != {pi_spec_hash}"
            )
        return entry
    new_entry = {
        "pi_id": pi_id,
        "pi_version": pi_version,
        "pi_spec_hash": pi_spec_hash,
        "obs_space": obs_space,
    }
    if description:
        new_entry["description"] = description
    registry["pi"].setdefault(pi_id, []).append(new_entry)
    return new_entry


def check_entry(
    registry: Dict[str, Any],
    *,
    pi_id: str,
    pi_version: str,
    pi_spec_hash: str,
) -> None:
    entry = find_entry(registry, pi_id, pi_version)
    if not entry:
        raise ValueError(f"Registry missing entry for {pi_id}@{pi_version}")
    if entry.get("pi_spec_hash") != pi_spec_hash:
        raise ValueError(
            f"Registry drift for {pi_id}@{pi_version}: "
            f"{entry.get('pi_spec_hash')} != {pi_spec_hash}"
        )

