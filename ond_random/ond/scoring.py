from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from .metrics import ONDProfile


@dataclass
class ONDTarget:
    mean: Dict[str, float]
    std: Dict[str, float]
    description: str = ""

    def as_dict(self) -> Dict[str, float | str]:
        return {"mean": self.mean, "std": self.std, "description": self.description}


@dataclass
class ONDScoreResult:
    distance: float
    score: float
    components: Dict[str, float]

    def as_dict(self) -> Dict[str, float | Dict[str, float]]:
        return {"distance": self.distance, "score": self.score, "components": self.components}


def _profile_dict(profile: ONDProfile | Dict[str, float]) -> Dict[str, float]:
    if isinstance(profile, ONDProfile):
        return {"H_rank": profile.h_rank, "H_sub": profile.h_sub, "H_branch": profile.h_branch}
    return {"H_rank": float(profile["H_rank"]), "H_sub": float(profile["H_sub"]), "H_branch": float(profile["H_branch"])}


def score_profile(
    profile: ONDProfile | Dict[str, float],
    target: ONDTarget | None = None,
    weights: Dict[str, float] | None = None,
) -> ONDScoreResult:
    """Compute OND score against a target.

    Score is 100 / (1 + distance), where distance is weighted L2 of z-scores.
    Higher score is better; 100 is ideal (distance = 0).
    """

    p = _profile_dict(profile)
    if target is None:
        target = ONDTarget(mean={"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0}, std={"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0})
    if weights is None:
        weights = {"H_rank": 1.0, "H_sub": 1.0, "H_branch": 1.0}

    components = {}
    dist = 0.0
    for key in ("H_rank", "H_sub", "H_branch"):
        mu = float(target.mean.get(key, 1.0))
        sigma = float(target.std.get(key, 1.0))
        if sigma <= 0.0:
            sigma = 1e-6
        w = float(weights.get(key, 1.0))
        z = (p[key] - mu) / sigma
        components[key] = z
        dist += w * (z ** 2)
    distance = dist ** 0.5
    score = 100.0 / (1.0 + distance)
    return ONDScoreResult(distance=distance, score=score, components=components)
