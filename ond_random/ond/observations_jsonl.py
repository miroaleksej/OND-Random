from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from .fileio import parse_int_auto

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1
SAFE_INT_MAX = 2**53 - 1


@dataclass
class ObservationsMeta:
    pi_id: str
    pi_version: str
    pi_spec_hash: str
    obs_space: Dict[str, Any]
    spec: Dict[str, Any] | None = None
    context: Dict[str, Any] | None = None
    public_context_hash: str | None = None
    extras: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": "meta",
            "pi_id": self.pi_id,
            "pi_version": self.pi_version,
            "pi_spec_hash": self.pi_spec_hash,
            "obs_space": self.obs_space,
        }
        if self.spec:
            data["spec"] = self.spec
        if self.context:
            data["context"] = self.context
        if self.public_context_hash:
            data["public_context_hash"] = self.public_context_hash
        if self.extras:
            data.update(self.extras)
        return data


def _json_safe_value(value: Any, stringify_large_ints: bool) -> Any:
    if isinstance(value, (np.floating, float)):
        return float(value)
    if isinstance(value, (np.integer, int)):
        v = int(value)
        if stringify_large_ints and abs(v) > SAFE_INT_MAX:
            return str(v)
        return v
    return value


def _parse_number_auto(value: Any) -> float | int:
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        # Integer pattern (decimal or hex)
        if re.fullmatch(r"[+-]?(0[xX][0-9a-fA-F]+|\d+)", text):
            return parse_int_auto(text)
        try:
            return float(text)
        except ValueError:
            raise ValueError(f"Cannot parse numeric value: {value!r}")
    raise ValueError(f"Unsupported numeric type: {type(value)}")


def write_observations_jsonl(
    path: str,
    U: np.ndarray,
    meta: ObservationsMeta,
    *,
    stringify_large_ints: bool = True,
    include_index: bool = True,
) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(meta.to_dict(), ensure_ascii=False) + "\n")
        for i, row in enumerate(U):
            row_arr = np.asarray(row).reshape(-1)
            values = [_json_safe_value(x, stringify_large_ints) for x in row_arr]
            record: Dict[str, Any] = {"type": "obs", "u": values}
            if include_index:
                record["i"] = i
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_observations_jsonl(path: str) -> Tuple[Dict[str, Any], np.ndarray, int]:
    meta: Dict[str, Any] = {}
    rows: List[List[float | int]] = []
    invalid_count = 0
    dim: int | None = None
    saw_meta = False

    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                invalid_count += 1
                continue
            if not isinstance(obj, dict):
                invalid_count += 1
                continue

            if obj.get("type") == "meta" or ("pi_id" in obj and "pi_version" in obj):
                if not saw_meta:
                    meta = obj
                    saw_meta = True
                continue

            if obj.get("valid") is False:
                invalid_count += 1
                continue

            values = obj.get("u", obj.get("obs"))
            if values is None or not isinstance(values, list):
                invalid_count += 1
                continue

            try:
                parsed = [_parse_number_auto(v) for v in values]
            except ValueError:
                invalid_count += 1
                continue

            if dim is None:
                dim = len(parsed)
            elif len(parsed) != dim:
                invalid_count += 1
                continue

            rows.append(parsed)

    if not rows:
        return meta, np.empty((0, dim or 0), dtype=float), invalid_count

    any_float = any(isinstance(v, float) for row in rows for v in row)
    any_bigint = any(isinstance(v, int) and (v < INT64_MIN or v > INT64_MAX) for row in rows for v in row)
    if any_float:
        U = np.array(rows, dtype=float)
    elif any_bigint:
        U = np.array(rows, dtype=object)
    else:
        U = np.array(rows, dtype=np.int64)
    return meta, U, invalid_count

