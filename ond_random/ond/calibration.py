from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

from .benchmark import ONDClass
from .scoring import ONDTarget


def calibrate_from_profiles(
    profiles: Iterable[Dict[str, float]],
    description: str = "calibrated",
) -> ONDTarget:
    values = {"H_rank": [], "H_sub": [], "H_branch": []}
    for p in profiles:
        values["H_rank"].append(float(p["H_rank"]))
        values["H_sub"].append(float(p["H_sub"]))
        values["H_branch"].append(float(p["H_branch"]))
    mean = {k: sum(v) / len(v) for k, v in values.items()}
    std = {}
    for k, v in values.items():
        if len(v) <= 1:
            std[k] = 0.05
        else:
            m = mean[k]
            std[k] = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
    return ONDTarget(mean=mean, std=std, description=description)


def load_profiles_from_benchmark_dir(path: str) -> list[Dict[str, float]]:
    base = Path(path)
    if not base.exists():
        raise FileNotFoundError(path)
    profiles = []
    for json_path in base.glob("*.json"):
        if json_path.name == "reference_profiles.json":
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        if "H_rank" in data:
            profiles.append(data)
    if not profiles:
        raise ValueError("no profiles found in benchmark dir")
    return profiles


def calibrate_from_benchmark_dir(path: str, target_class: ONDClass = ONDClass.I) -> ONDTarget:
    profiles = load_profiles_from_benchmark_dir(path)
    subset = [p for p in profiles if p.get("ond_class") == target_class.value]
    if not subset:
        raise ValueError(f"no profiles for class {target_class.value}")
    return calibrate_from_profiles(subset, description=f"bench-{target_class.value}")
