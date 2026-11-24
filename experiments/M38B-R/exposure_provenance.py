"""Declared exposure provenance, uncertainty bounds and in-memory SHA-256 chain.

This is a pre-outcome engineering audit wrapper around CadenceLedger.
Identifiers, time bounds and uncertainties come from an UNTRUSTED producer.
SHA-256 detects internal changes to recorded copies; it authenticates
neither a telescope nor a clock, and it is not a signature or keyed MAC.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

import numpy as np

from sequential_cadence import CadenceLedger


_DOMAIN = b"ARARA-M38BR-P07-CHAIN-v1\x00"
_GENESIS = bytes(32)


@dataclass(frozen=True)
class ExposureRecord:
    cadence_index: int
    session_id: str
    instrument_id: str
    target_id: str
    clock_id: str
    start_seconds: float
    end_seconds: float
    start_uncertainty_seconds: float
    end_uncertainty_seconds: float
    digest: str


def _digest(previous: bytes, record: ExposureRecord, frame: np.ndarray) -> bytes:
    """Canonical metadata and little-endian binary64 frame payload."""
    metadata = {
        "format": "arara-m38br-p07-v1",
        "cadence_index": record.cadence_index,
        "session_id": record.session_id,
        "instrument_id": record.instrument_id,
        "target_id": record.target_id,
        "clock_id": record.clock_id,
        "start_seconds": record.start_seconds,
        "end_seconds": record.end_seconds,
        "start_uncertainty_seconds": record.start_uncertainty_seconds,
        "end_uncertainty_seconds": record.end_uncertainty_seconds,
        "frame_shape": list(frame.shape),
        "frame_dtype": "little-endian-float64",
    }
    encoded = json.dumps(
        metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    binary = np.array(frame, dtype="<f8", order="C", copy=True).tobytes(order="C")
    h = hashlib.sha256()
    h.update(_DOMAIN)
    h.update(previous)
    h.update(len(encoded).to_bytes(4, "big"))
    h.update(encoded)
    h.update(binary)
    return h.digest()


class ExposureProvenanceLedger:
    """Validate declared exposure envelopes, then score only accepted prefixes.

    Uncertainties are asserted *absolute time error bounds* in unverified
    seconds. They are not probabilistic standard deviations. The wrapper
    is irreversibly blocked on any invalid frame or metadata declaration.
    """

    def __init__(
        self, *, curves: int, stars_per_curve: int,
        session_id: str, instrument_id: str, target_id: str, clock_id: str,
    ) -> None:
        # Constructor failure does not create a usable session.
        for field, value in (
            ("session_id", session_id), ("instrument_id", instrument_id),
            ("target_id", target_id), ("clock_id", clock_id),
        ):
            if type(value) is not str or not value.strip() or len(value) > 128:
                raise ValueError(f"Expected a nonempty identifier of <=128 characters: {field}")
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as error:
                raise ValueError(f"Identifier must be valid UTF-8: {field}") from error
        self._cadences = CadenceLedger(
            curves=curves, stars_per_curve=stars_per_curve
        )
        self._session_id = session_id
        self._instrument_id = instrument_id
        self._target_id = target_id
        self._clock_id = clock_id
        self._records: list[ExposureRecord] = []
        self._blocked_reason: str | None = None

    @property
    def blocked(self) -> bool:
        return self._blocked_reason is not None or self._cadences.blocked

    @property
    def blocked_reason(self) -> str | None:
        return self._blocked_reason or self._cadences.blocked_reason

    @property
    def count(self) -> int:
        return self._cadences.count

    @property
    def records(self) -> tuple[ExposureRecord, ...]:
        """Immutable record copies; identities and times are not authenticated."""
        return tuple(self._records)

    def _reject(self, message: str) -> None:
        self._blocked_reason = message
        raise ValueError(message)

    def _ensure_active(self) -> None:
        if self.blocked:
            raise ValueError(
                "Exposure provenance ledger is permanently blocked: "
                + str(self.blocked_reason)
            )

    def _number(self, value: float, label: str, *, nonnegative: bool = False) -> float:
        if type(value) not in (int, float):
            self._reject(f"{label} must be a Python finite real number")
        try:
            cast = float(value)
        except (TypeError, ValueError, OverflowError):
            self._reject(f"{label} cannot be represented as float64")
        if not math.isfinite(cast) or (nonnegative and cast < 0.0):
            self._reject(f"{label} must be finite and nonnegative" if nonnegative
                         else f"{label} must be finite")
        return cast

    def append(
        self, *, cadence_index: int, frame: np.ndarray,
        instrument_id: str, target_id: str, clock_id: str,
        start_seconds: float, end_seconds: float,
        start_uncertainty_seconds: float, end_uncertainty_seconds: float,
    ) -> None:
        """Append a complete declared exposure or permanently block this session."""
        self._ensure_active()
        if instrument_id != self._instrument_id:
            self._reject("Declared instrument identity changed")
        if target_id != self._target_id:
            self._reject("Declared target identity changed")
        if clock_id != self._clock_id:
            self._reject("Declared clock identity changed")

        start = self._number(start_seconds, "Exposure start")
        end = self._number(end_seconds, "Exposure end")
        start_error = self._number(
            start_uncertainty_seconds, "Start uncertainty", nonnegative=True
        )
        end_error = self._number(
            end_uncertainty_seconds, "End uncertainty", nonnegative=True
        )
        latest_possible_start = start + start_error
        earliest_possible_end = end - end_error
        earliest_possible_start = start - start_error
        latest_possible_end = end + end_error
        midpoint = start / 2.0 + end / 2.0
        if not all(map(math.isfinite, (
            latest_possible_start, earliest_possible_end,
            earliest_possible_start, latest_possible_end, midpoint,
        ))):
            self._reject("Nonfinite derived exposure bounds")
        if not latest_possible_start < earliest_possible_end:
            self._reject("Exposure is not definitely positive with uncertainty")
        if self._records:
            previous = self._records[-1]
            previous_last_end = (
                previous.end_seconds + previous.end_uncertainty_seconds
            )
            if not math.isfinite(previous_last_end):
                self._reject("Nonfinite previous exposure bound")
            if not previous_last_end < earliest_possible_start:
                self._reject("Exposure time bounds overlap or ordering is ambiguous")

        # The downstream P0.6 ledger checks the exact next cadence,
        # midpoint ordering and finite frame shape; an invalid append
        # leaves its segment blocked. No metadata record is committed then.
        try:
            self._cadences.append(
                cadence_index=cadence_index,
                timestamp_seconds=midpoint,
                frame=frame,
            )
        except ValueError:
            self._blocked_reason = (
                self._cadences.blocked_reason
                or "Underlying cadence append rejected"
            )
            raise

        record = ExposureRecord(
            cadence_index=cadence_index,
            session_id=self._session_id,
            instrument_id=self._instrument_id,
            target_id=self._target_id,
            clock_id=self._clock_id,
            start_seconds=start,
            end_seconds=end,
            start_uncertainty_seconds=start_error,
            end_uncertainty_seconds=end_error,
            digest="",
        )
        # The P0.6 ledger owns a float64 copy, not the caller's mutable frame.
        accepted = self._cadences.snapshot()[:, :, -1]
        previous_digest = bytes.fromhex(self._records[-1].digest) if self._records else _GENESIS
        digest = _digest(previous_digest, record, accepted).hex()
        from dataclasses import replace
        self._records.append(replace(record, digest=digest))

    def verify_integrity(self) -> str:
        """Verify consistency of stored metadata/frame bytes; never authenticity."""
        self._ensure_active()
        if not self._records or len(self._records) != self._cadences.count:
            self._reject("Record/frame count inconsistency")
        frames = self._cadences.snapshot()
        previous = _GENESIS
        for index, record in enumerate(self._records):
            if record.cadence_index != index:
                self._reject("Stored cadence record order changed")
            try:
                computed = _digest(previous, record, frames[:, :, index])
            except (ValueError, OverflowError, UnicodeError):
                self._reject("Stored exposure record cannot be re-encoded")
            if computed.hex() != record.digest:
                self._reject("Stored exposure record digest mismatch")
            previous = computed
        return previous.hex()

    def snapshot(self) -> np.ndarray:
        """Return a copy of accepted raw frames after verifying the chain."""
        self.verify_integrity()
        return self._cadences.snapshot()

    def score_latest(self) -> dict[str, np.ndarray]:
        """Uncalibrated prefix score after metadata/frame consistency checks."""
        self.verify_integrity()
        return self._cadences.score_latest()
