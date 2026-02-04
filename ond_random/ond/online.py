from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable

from .scoring import ONDTarget


@dataclass
class OnlineCalibrator:
    """Online calibration for OND metrics using Welford updates."""

    metrics: tuple[str, ...] = ("H_rank", "H_sub", "H_branch")
    min_std: float = 0.05
    count: int = 0
    mean: Dict[str, float] = field(default_factory=dict)
    m2: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in self.metrics:
            self.mean.setdefault(k, 0.0)
            self.m2.setdefault(k, 0.0)

    def update(self, profile: Dict[str, float]) -> None:
        self.count += 1
        for k in self.metrics:
            if k not in profile:
                continue
            x = float(profile[k])
            delta = x - self.mean[k]
            self.mean[k] += delta / self.count
            delta2 = x - self.mean[k]
            self.m2[k] += delta * delta2

    def update_many(self, profiles: Iterable[Dict[str, float]]) -> None:
        for p in profiles:
            self.update(p)

    def std(self) -> Dict[str, float]:
        std = {}
        for k in self.metrics:
            if self.count <= 1:
                std[k] = self.min_std
            else:
                var = self.m2[k] / (self.count - 1)
                std[k] = max(self.min_std, var ** 0.5)
        return std

    def target(self, description: str = "online") -> ONDTarget:
        return ONDTarget(mean=dict(self.mean), std=self.std(), description=description)

    def as_dict(self) -> Dict[str, float | int | Dict[str, float]]:
        return {
            "count": self.count,
            "mean": dict(self.mean),
            "std": self.std(),
        }

    def state_dict(self) -> Dict[str, float | int | Dict[str, float] | list[str]]:
        return {
            "count": self.count,
            "mean": dict(self.mean),
            "m2": dict(self.m2),
            "metrics": list(self.metrics),
            "min_std": self.min_std,
        }

    @classmethod
    def from_state(cls, state: Dict[str, float | int | Dict[str, float] | list[str]]) -> "OnlineCalibrator":
        metrics = tuple(state.get("metrics", ("H_rank", "H_sub", "H_branch")))  # type: ignore[arg-type]
        min_std = float(state.get("min_std", 0.05))  # type: ignore[arg-type]
        cal = cls(metrics=metrics, min_std=min_std)
        cal.count = int(state.get("count", 0))  # type: ignore[arg-type]
        mean = state.get("mean", {})  # type: ignore[arg-type]
        m2 = state.get("m2", {})  # type: ignore[arg-type]
        cal.mean.update({k: float(v) for k, v in mean.items()})
        cal.m2.update({k: float(v) for k, v in m2.items()})
        cal.__post_init__()
        return cal
