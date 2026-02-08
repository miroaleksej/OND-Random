from __future__ import annotations

from typing import Any, Dict


SUPPORTED_SCHEMA_VERSIONS = {"0.1"}
SUPPORTED_SPEC_VERSIONS = {"0.1"}


def _coerce_version(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value.strip()
    return None


def is_supported_schema_version(version: Any) -> bool:
    v = _coerce_version(version)
    if v is None:
        return False
    major = v.split(".", 1)[0]
    return major == "0"


def is_supported_spec_version(version: Any) -> bool:
    v = _coerce_version(version)
    if v is None:
        return False
    major = v.split(".", 1)[0]
    return major == "0"


def compatibility_notes(spec: Dict[str, Any] | None) -> list[str]:
    if not isinstance(spec, dict):
        return ["spec_missing_or_invalid"]
    notes = []
    spec_v = spec.get("spec_version")
    schema_v = spec.get("schema_version")
    if not is_supported_spec_version(spec_v):
        notes.append(f"unsupported_spec_version:{spec_v}")
    if not is_supported_schema_version(schema_v):
        notes.append(f"unsupported_schema_version:{schema_v}")
    return notes
