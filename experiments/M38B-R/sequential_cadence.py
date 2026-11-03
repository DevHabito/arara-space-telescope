"""Fail-closed sequential cadence ledger for pre-outcome software tests.

The ledger only verifies the caller's declared order and timestamp monotonicity.
It does not authenticate camera clocks, exposure boundaries, or sensor origins.
A rejected append permanently blocks that ledger; no gaps are imputed.
"""
from __future__ import annotations

import math

import numpy as np

from observed_prefix import score_observed_prefix


class CadenceLedger:
    """Own consecutive, finite frames and score only the latest measured prefix."""

    def __init__(self, *, curves: int, stars_per_curve: int) -> None:
        if type(curves) is not int or curves < 1:
            raise ValueError("Expected a positive integer curve count")
        if type(stars_per_curve) is not int or stars_per_curve < 2:
            raise ValueError("Expected at least two stars per curve")
        self._curves = curves
        self._stars_per_curve = stars_per_curve
        self._frames: list[np.ndarray] = []
        self._declared_times: list[float] = []
        self._blocked_reason: str | None = None

    @property
    def count(self) -> int:
        return len(self._frames)

    @property
    def latest_index(self) -> int:
        return self.count - 1

    @property
    def declared_times(self) -> tuple[float, ...]:
        """Caller-supplied ordering metadata, not authenticated instrument times."""
        return tuple(self._declared_times)

    @property
    def blocked(self) -> bool:
        return self._blocked_reason is not None

    @property
    def blocked_reason(self) -> str | None:
        return self._blocked_reason

    def _reject(self, reason: str) -> None:
        self._blocked_reason = reason
        raise ValueError(reason)

    def _ensure_active(self) -> None:
        if self.blocked:
            raise ValueError(
                "Cadence ledger is permanently blocked: " + str(self._blocked_reason)
            )

    def append(
        self, *, cadence_index: int, timestamp_seconds: float,
        frame: np.ndarray
    ) -> None:
        """Accept one contiguous finite frame, or block the segment permanently.

        All validations occur before the frame and its time declaration are
        committed together. A rejected frame is never added to the ledger.
        """
        self._ensure_active()
        if type(cadence_index) is not int or not 0 <= cadence_index <= 179:
            self._reject("Cadence index must be an integer in 0..179")
        if cadence_index != self.count:
            self._reject(
                f"Expected next cadence index {self.count}, got {cadence_index}; "
                "gaps, duplicates and reordering are not permitted"
            )
        if type(timestamp_seconds) not in (int, float):
            self._reject("Declared timestamp must be a Python finite number")
        try:
            stated_time = float(timestamp_seconds)
        except (ValueError, OverflowError):
            self._reject("Declared timestamp cannot be represented as finite float")
        if not math.isfinite(stated_time):
            self._reject("Declared timestamp must be finite")
        if self._declared_times and stated_time <= self._declared_times[-1]:
            self._reject("Declared timestamps must be strictly increasing")

        # Inspect and convert in separate guarded steps. NumPy may raise
        # ValueError for ragged nested sequences before shape inspection.
        # Every failed conversion must block the ledger, not just fail a call.
        try:
            received = np.asarray(frame)
        except (TypeError, ValueError, OverflowError):
            self._reject("Cannot inspect observed frame structure")
        if received.shape != (self._curves, self._stars_per_curve):
            self._reject("Observed frame must have fixed (curve, star) dimensions")
        if received.dtype.kind not in "iuf":
            self._reject("Observed frame must contain numeric real samples")
        try:
            copied = np.array(received, dtype=np.float64, copy=True)
        except (TypeError, ValueError, OverflowError):
            self._reject("Cannot convert observed frame to finite float64")
        if not np.isfinite(copied).all():
            self._reject("Observed frame must be entirely finite")

        copied.setflags(write=False)
        self._frames.append(copied)
        self._declared_times.append(stated_time)

    def snapshot(self) -> np.ndarray:
        """Return a new array for the latest accepted prefix only."""
        self._ensure_active()
        if not self._frames:
            raise ValueError("No accepted measured frames in this ledger")
        return np.stack(self._frames, axis=-1)

    def score_latest(self) -> dict[str, np.ndarray]:
        """Use only the currently accepted prefix; never a future-filled array."""
        self._ensure_active()
        endpoint = self.latest_index
        if endpoint < 81:
            raise ValueError("At least cadences 0..81 must be measured before scoring")
        return score_observed_prefix(self.snapshot(), endpoint=endpoint)
