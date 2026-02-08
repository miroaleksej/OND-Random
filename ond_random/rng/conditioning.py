from __future__ import annotations

import math
from typing import Dict, Optional


def toeplitz_required_min_entropy(output_bits: int, epsilon: float) -> float:
    if output_bits <= 0:
        raise ValueError("output_bits must be positive")
    if not (0.0 < epsilon < 1.0):
        raise ValueError("epsilon must be in (0, 1)")
    return float(output_bits + 2.0 * math.log2(1.0 / epsilon))


def evaluate_toeplitz_conditioning(
    output_bits: int,
    epsilon: float,
    observed_min_entropy_bits: Optional[float] = None,
) -> Dict[str, Optional[float]]:
    required = toeplitz_required_min_entropy(output_bits, epsilon)
    margin = None
    status = "unknown"
    if observed_min_entropy_bits is not None:
        margin = float(observed_min_entropy_bits - required)
        status = "sufficient" if margin >= 0 else "insufficient"
    return {
        "required_min_entropy_bits": required,
        "observed_min_entropy_bits": observed_min_entropy_bits,
        "margin_bits": margin,
        "status": status,
    }
