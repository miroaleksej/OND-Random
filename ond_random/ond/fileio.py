from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


def parse_int_auto(value: str | int | float) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    text = str(value).strip()
    if text.startswith(("0x", "0X")):
        return int(text, 16)
    # Heuristic: treat as hex if it contains hex letters
    if any(c in text for c in "abcdefABCDEF"):
        return int(text, 16)
    return int(text)


def load_npy(path: str) -> np.ndarray:
    return np.load(path, allow_pickle=True)


def load_npz(path: str, key: str = "U") -> np.ndarray:
    with np.load(path, allow_pickle=True) as data:
        if key not in data:
            raise KeyError(f"npz key not found: {key}")
        return data[key]


def _iter_csv_rows(path: str, delimiter: str = ",") -> Iterable[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            yield {k: (v.strip() if isinstance(v, str) else str(v)) for k, v in row.items()}


def load_csv_matrix(path: str, columns: Sequence[str], delimiter: str = ",") -> np.ndarray:
    if not columns:
        raise ValueError("columns must be non-empty")
    rows = []
    for row in _iter_csv_rows(path, delimiter=delimiter):
        rows.append([float(row[c]) for c in columns])
    return np.asarray(rows, dtype=float)


def load_csv_series(path: str, column: str, delimiter: str = ",") -> np.ndarray:
    if not column:
        raise ValueError("column must be non-empty")
    values = []
    for row in _iter_csv_rows(path, delimiter=delimiter):
        values.append(float(row[column]))
    return np.asarray(values, dtype=float)


def load_text_series_regex(path: str, pattern: str) -> np.ndarray:
    if not pattern:
        raise ValueError("pattern must be non-empty")
    rx = re.compile(pattern)
    out = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = rx.search(line)
        if not m:
            continue
        if m.lastindex is None:
            raise ValueError("regex must contain a capturing group for the numeric value")
        out.append(float(m.group(1)))
    return np.asarray(out, dtype=float)


def load_ecdsa_rsz_csv(
    path: str,
    n: int,
    r_col: str = "r",
    s_col: str = "s",
    z_col: str = "z",
    delimiter: str = ",",
) -> np.ndarray:
    if n <= 0:
        raise ValueError("n must be positive")
    points = []
    for row in _iter_csv_rows(path, delimiter=delimiter):
        r = parse_int_auto(row[r_col]) % n
        s = parse_int_auto(row[s_col]) % n
        z = parse_int_auto(row[z_col]) % n
        if s == 0:
            raise ValueError("invalid signature: s == 0 (not invertible)")
        inv_s = pow(s, -1, n)
        u_r = (r * inv_s) % n
        u_z = (z * inv_s) % n
        points.append((u_r, u_z))
    return np.asarray(points, dtype=object)

