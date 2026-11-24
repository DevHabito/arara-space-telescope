"""P0.8 keyed packet-custody audit; never an instrument authentication service.

HMAC-SHA-256 authenticates possession of a provisioned symmetric key.
This module does NOT provision keys, attest sensor hardware, calibrate
clocks, certify target identity, persist an audit log or prevent replay
of a whole transcript in a new verifier with the same session/key.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import hmac
import json

import numpy as np

from exposure_provenance import ExposureProvenanceLedger


_DOMAIN = b"ARARA-M38BR-P08-PACKET-v1\x00"
_GENESIS_MAC_HEX = "0" * 64
_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class AuthenticatedPacket:
    """Byte-preserving numeric transport record, not raw camera ADC/FITS."""

    cadence_index: int
    key_id: str
    session_id: str
    instrument_id: str
    target_id: str
    clock_id: str
    frame_shape: tuple[int, int]
    start_seconds: float
    end_seconds: float
    start_uncertainty_seconds: float
    end_uncertainty_seconds: float
    raw_frame_bytes: bytes
    previous_mac_hex: str
    mac_hex: str


def _message_bytes(packet: AuthenticatedPacket) -> bytes:
    """Unambiguous versioned framing of signed metadata and exact frame bytes."""
    meta = {
        "version": "arara-m38br-p08-v1",
        "cadence_index": packet.cadence_index,
        "key_id": packet.key_id,
        "session_id": packet.session_id,
        "instrument_id": packet.instrument_id,
        "target_id": packet.target_id,
        "clock_id": packet.clock_id,
        "frame_shape": list(packet.frame_shape),
        "raw_format": "little-endian-binary64-C",
        "start_seconds": packet.start_seconds,
        "end_seconds": packet.end_seconds,
        "start_uncertainty_seconds": packet.start_uncertainty_seconds,
        "end_uncertainty_seconds": packet.end_uncertainty_seconds,
        "previous_mac_hex": packet.previous_mac_hex,
    }
    metadata = json.dumps(
        meta, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    raw = packet.raw_frame_bytes
    return (
        _DOMAIN + len(metadata).to_bytes(4, "big") + metadata
        + len(raw).to_bytes(4, "big") + raw
    )


def _calculate_mac(packet: AuthenticatedPacket, key: bytes) -> bytes:
    """Use standard-library HMAC, not a custom home-made MAC."""
    return hmac.new(key, _message_bytes(packet), hashlib.sha256).digest()


def seal_software_test_packet(
    packet: AuthenticatedPacket, *, public_fixture_key: bytes
) -> AuthenticatedPacket:
    """Create controlled test packets; this is NOT a trusted device signer.

    The deliberately public key in tests cannot authenticate a telescope.
    This helper is not a deployment credential or secure key-issuance path.
    """
    if type(public_fixture_key) is not bytes or len(public_fixture_key) < 32:
        raise ValueError("A software fixture requires at least 32 key bytes")
    if type(packet.raw_frame_bytes) is not bytes:
        raise ValueError("Packet frame must already be immutable bytes")
    return replace(
        packet, mac_hex=_calculate_mac(packet, public_fixture_key).hex()
    )


def _is_lower_hex_64(value: object) -> bool:
    return (
        type(value) is str and len(value) == 64
        and all(character in _HEX for character in value)
    )


class KeyedCustodyVerifier:
    """Fail-closed in-memory receiver, pinned to externally supplied claims.

    A valid MAC establishes only knowledge of the correct symmetric key.
    The verifier cannot know who actually measured or fabricated the data.
    """

    def __init__(
        self, *, curves: int, stars_per_curve: int, session_id: str,
        instrument_id: str, target_id: str, clock_id: str,
        key_id: str, verification_key: bytes,
    ) -> None:
        if type(key_id) is not str or not key_id.strip() or len(key_id) > 128:
            raise ValueError("Expected a nonempty pinned key identifier")
        if type(verification_key) is not bytes or len(verification_key) < 32:
            raise ValueError("Verification key must be at least 32 secret bytes")
        self._inner = ExposureProvenanceLedger(
            curves=curves, stars_per_curve=stars_per_curve,
            session_id=session_id, instrument_id=instrument_id,
            target_id=target_id, clock_id=clock_id,
        )
        self._key_id = key_id
        self._key = bytes(verification_key)
        self._session_id = session_id
        self._instrument_id = instrument_id
        self._target_id = target_id
        self._clock_id = clock_id
        self._shape = (curves, stars_per_curve)
        self._packets: list[AuthenticatedPacket] = []
        self._blocked_reason: str | None = None

    @property
    def blocked(self) -> bool:
        return self._blocked_reason is not None or self._inner.blocked

    @property
    def blocked_reason(self) -> str | None:
        return self._blocked_reason or self._inner.blocked_reason

    @property
    def count(self) -> int:
        return self._inner.count

    @property
    def packets(self) -> tuple[AuthenticatedPacket, ...]:
        """Immutable copies of original signed numeric bytes; no secret key."""
        return tuple(self._packets)

    def _reject(self, message: str) -> None:
        self._blocked_reason = message
        raise ValueError(message)

    def _active(self) -> None:
        if self.blocked:
            raise ValueError("Keyed custody verifier permanently blocked: "
                             + str(self.blocked_reason))

    def _expected_previous(self) -> str:
        return self._packets[-1].mac_hex if self._packets else _GENESIS_MAC_HEX

    def _verify_packet_mac(self, packet: AuthenticatedPacket) -> None:
        if type(packet) is not AuthenticatedPacket:
            self._reject("Expected an authenticated packet record")
        if type(packet.cadence_index) is not int or packet.cadence_index != self.count:
            self._reject("Signed packet has duplicate, missing or reordered cadence")
        for field, pinned in (
            ("session_id", self._session_id),
            ("instrument_id", self._instrument_id),
            ("target_id", self._target_id),
            ("clock_id", self._clock_id),
            ("key_id", self._key_id),
        ):
            if getattr(packet, field) != pinned:
                self._reject(f"Signed packet has an unexpected {field}")
        if packet.frame_shape != self._shape or type(packet.frame_shape) is not tuple:
            self._reject("Signed packet frame shape is not pinned")
        if type(packet.raw_frame_bytes) is not bytes:
            self._reject("Signed packet must contain exact immutable frame bytes")
        if len(packet.raw_frame_bytes) != self._shape[0] * self._shape[1] * 8:
            self._reject("Signed packet frame byte length mismatch")
        if packet.previous_mac_hex != self._expected_previous():
            self._reject("Signed packet chain predecessor mismatch")
        if not _is_lower_hex_64(packet.mac_hex):
            self._reject("Malformed HMAC tag")

        try:
            expected = _calculate_mac(packet, self._key)
        except (ValueError, TypeError, OverflowError, UnicodeError):
            self._reject("Signed packet has noncanonical metadata")
        if not hmac.compare_digest(expected, bytes.fromhex(packet.mac_hex)):
            self._reject("Signed packet HMAC verification failed")

    def append(self, packet: AuthenticatedPacket) -> None:
        """Verify MAC on exact supplied bytes *before* numeric decoding."""
        self._active()
        self._verify_packet_mac(packet)
        try:
            samples = np.frombuffer(
                packet.raw_frame_bytes, dtype="<f8"
            ).reshape(self._shape).copy()
        except (ValueError, TypeError, OverflowError):
            self._reject("Authenticated frame cannot be decoded as binary64")
        if not np.isfinite(samples).all():
            self._reject("Authenticated frame has nonfinite measured samples")

        try:
            self._inner.append(
                cadence_index=packet.cadence_index,
                frame=samples,
                instrument_id=packet.instrument_id,
                target_id=packet.target_id,
                clock_id=packet.clock_id,
                start_seconds=packet.start_seconds,
                end_seconds=packet.end_seconds,
                start_uncertainty_seconds=packet.start_uncertainty_seconds,
                end_uncertainty_seconds=packet.end_uncertainty_seconds,
            )
        except (ValueError, TypeError, OverflowError):
            self._reject("P0.7 exposure/measurement contract rejected signed packet")
        self._packets.append(packet)

    def verify_custody(self) -> str:
        """Check recorded MACs and correspondence to P0.7 accepted copies."""
        self._active()
        if not self._packets or len(self._packets) != self._inner.count:
            self._reject("Signed packet count does not match exposure ledger")
        previous = _GENESIS_MAC_HEX
        recorded = self._inner.snapshot()
        for index, packet in enumerate(self._packets):
            if packet.cadence_index != index or packet.previous_mac_hex != previous:
                self._reject("Stored signed packet cadence chain changed")
            try:
                expected = _calculate_mac(packet, self._key)
            except (ValueError, TypeError, OverflowError, UnicodeError):
                self._reject("Stored signed packet metadata invalid")
            if not _is_lower_hex_64(packet.mac_hex):
                self._reject("Stored signed packet MAC is malformed")
            if not hmac.compare_digest(expected, bytes.fromhex(packet.mac_hex)):
                self._reject("Stored signed packet MAC mismatch")
            # A retagged malformed stored packet must still poison the
            # session; NumPy's frombuffer can raise before an array exists.
            if (
                type(packet.raw_frame_bytes) is not bytes
                or len(packet.raw_frame_bytes) != self._shape[0] * self._shape[1] * 8
            ):
                self._reject("Stored signed packet byte length mismatch")
            try:
                signed = np.frombuffer(packet.raw_frame_bytes, dtype="<f8")
            except (TypeError, ValueError, BufferError):
                self._reject("Stored signed packet cannot be decoded")
            if signed.size != self._shape[0] * self._shape[1]:
                self._reject("Stored signed packet length mismatch")
            source_bytes = np.array(
                recorded[:, :, index], dtype="<f8", order="C", copy=True
            ).tobytes(order="C")
            if source_bytes != packet.raw_frame_bytes:
                self._reject("Signed packet and accepted numeric frame differ")
            previous = packet.mac_hex
        return previous

    def score_latest(self) -> dict[str, np.ndarray]:
        """Uncalibrated P0.5 score, after HMAC and P0.7 consistency checks."""
        self.verify_custody()
        return self._inner.score_latest()
