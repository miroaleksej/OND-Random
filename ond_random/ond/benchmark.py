from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable


class ONDClass(str, Enum):
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"


@dataclass
class ReferenceProfile:
    ond_class: ONDClass
    mean: Dict[str, float]
    std: Dict[str, float]
    description: str = ""

    def distance(self, profile: Dict[str, float]) -> float:
        dist = 0.0
        for key in ("H_rank", "H_sub", "H_branch"):
            mu = self.mean.get(key, 0.0)
            sigma = self.std.get(key, 1.0)
            if sigma <= 0:
                sigma = 1e-6
            diff = (profile.get(key, 0.0) - mu) / sigma
            dist += diff * diff
        return dist ** 0.5


DEFAULT_REFERENCES = [
    ReferenceProfile(
        ond_class=ONDClass.I,
        mean={"H_rank": 0.98, "H_sub": 0.95, "H_branch": 0.95},
        std={"H_rank": 0.05, "H_sub": 0.07, "H_branch": 0.07},
        description="OND-maximal (IID-like)",
    ),
    ReferenceProfile(
        ond_class=ONDClass.II,
        mean={"H_rank": 0.35, "H_sub": 0.80, "H_branch": 0.75},
        std={"H_rank": 0.20, "H_sub": 0.10, "H_branch": 0.12},
        description="Low-rank / recurrent dynamics",
    ),
    ReferenceProfile(
        ond_class=ONDClass.III,
        mean={"H_rank": 0.90, "H_sub": 0.35, "H_branch": 0.55},
        std={"H_rank": 0.07, "H_sub": 0.20, "H_branch": 0.20},
        description="Phase-restricted / clustered dynamics",
    ),
    ReferenceProfile(
        ond_class=ONDClass.IV,
        mean={"H_rank": 0.55, "H_sub": 0.45, "H_branch": 0.20},
        std={"H_rank": 0.25, "H_sub": 0.20, "H_branch": 0.15},
        description="Finite-state / automaton-like",
    ),
]


def classify_profile(profile: Dict[str, float], references: Iterable[ReferenceProfile] = DEFAULT_REFERENCES) -> ONDClass:
    best = None
    best_dist = float("inf")
    for ref in references:
        dist = ref.distance(profile)
        if dist < best_dist:
            best_dist = dist
            best = ref.ond_class
    return best or ONDClass.I


def load_reference_profiles(path: str) -> list[ReferenceProfile]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    refs = []
    for item in data:
        refs.append(
            ReferenceProfile(
                ond_class=ONDClass(item["ond_class"]),
                mean=item["mean"],
                std=item["std"],
                description=item.get("description", ""),
            )
        )
    return refs


def save_reference_profiles(path: str, references: Iterable[ReferenceProfile]) -> None:
    data = []
    for ref in references:
        data.append(
            {
                "ond_class": ref.ond_class.value,
                "mean": ref.mean,
                "std": ref.std,
                "description": ref.description,
            }
        )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
