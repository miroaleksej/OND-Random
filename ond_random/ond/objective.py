from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from .metrics import ONDProfile
from .scoring import ONDTarget


@dataclass
class ONDObjectiveResult:
    score: float
    distance: float
    stability: float
    weights: Dict[str, float]
    per_source: Dict[str, float]

    def as_dict(self) -> Dict[str, object]:
        return {
            "score": self.score,
            "distance": self.distance,
            "stability": self.stability,
            "weights": self.weights,
            "per_source": self.per_source,
        }


def _profile_values(profile: ONDProfile | Mapping[str, float]) -> Dict[str, float]:
    if isinstance(profile, ONDProfile):
        return {"H_rank": profile.h_rank, "H_sub": profile.h_sub, "H_branch": profile.h_branch}
    return {"H_rank": float(profile["H_rank"]), "H_sub": float(profile["H_sub"]), "H_branch": float(profile["H_branch"])}


def auto_weights_from_profiles(profiles: Mapping[str, ONDProfile | Mapping[str, float]]) -> Dict[str, float]:
    values = {"H_rank": [], "H_sub": [], "H_branch": []}
    for p in profiles.values():
        v = _profile_values(p)
        for k in values:
            values[k].append(v[k])
    weights = {}
    for k, arr in values.items():
        if len(arr) <= 1:
            weights[k] = 1.0
            continue
        mean = sum(arr) / len(arr)
        var = sum((x - mean) ** 2 for x in arr) / (len(arr) - 1)
        weights[k] = 1.0 / (var + 1e-6)
    return weights


def objective_from_profiles(
    profiles: Mapping[str, ONDProfile | Mapping[str, float]],
    target: ONDTarget,
    weights: Dict[str, float] | None = None,
    stability_weight: float = 1.0,
) -> ONDObjectiveResult:
    if weights is None:
        weights = {"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0}

    # Distance to target (mean across sources)
    per_source = {}
    for name, prof in profiles.items():
        v = _profile_values(prof)
        dist = 0.0
        for k in ("H_rank", "H_sub", "H_branch"):
            mu = float(target.mean.get(k, 1.0))
            sigma = float(target.std.get(k, 1.0))
            if sigma <= 0.0:
                sigma = 1e-6
            z = (v[k] - mu) / sigma
            dist += weights.get(k, 1.0) * (z ** 2)
        per_source[name] = dist ** 0.5
    mean_distance = sum(per_source.values()) / max(1, len(per_source))

    # Stability penalty = weighted std across sources
    stability = 0.0
    for k in ("H_rank", "H_sub", "H_branch"):
        arr = [ _profile_values(p)[k] for p in profiles.values() ]
        if len(arr) <= 1:
            continue
        mean = sum(arr) / len(arr)
        var = sum((x - mean) ** 2 for x in arr) / (len(arr) - 1)
        stability += weights.get(k, 1.0) * var
    stability = stability ** 0.5

    total = mean_distance + stability_weight * stability
    score = 100.0 / (1.0 + total)
    return ONDObjectiveResult(score=score, distance=mean_distance, stability=stability, weights=weights, per_source=per_source)
