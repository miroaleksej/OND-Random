from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence

import numpy as np


class ProtocolObservation(ABC):
    """Protocol-specific observation mapping to OND space."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def modulus(self) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def observe(self, signature, message=None) -> np.ndarray:
        """Return a 1D numpy array for a single signature."""
        raise NotImplementedError

    def observe_many(
        self,
        signatures: Sequence,
        messages: Sequence | None = None,
    ) -> np.ndarray:
        if messages is None:
            messages = [None] * len(signatures)
        if len(messages) != len(signatures):
            raise ValueError("messages length must match signatures length")
        rows = [self.observe(sig, msg) for sig, msg in zip(signatures, messages)]
        arr = np.array(rows, dtype=object)
        # Keep raw values; convert to float only for numeric compatibility if needed by caller.
        if self.modulus is not None and self.modulus > 2**63:
            return arr.astype(float)
        return arr
