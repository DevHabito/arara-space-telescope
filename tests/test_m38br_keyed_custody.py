"""P0.8 keyed custody tests, specified before implementation.

All labels, key bytes and samples are PUBLIC numerical test fixtures.
No production secret or astronomical observation is committed here.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import hmac
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments/M38B-R"))

from keyed_custody import (  # noqa: E402
    AuthenticatedPacket, KeyedCustodyVerifier, seal_software_test_packet,
)
from observed_prefix import score_observed_prefix  # noqa: E402

# Deliberately public example material. NOT suitable as deployed credentials.
PUBLIC_FIXTURE_KEY = b"PUBLIC-TEST-KEY-NOT-FOR-DEPLOYMENT-000001"
OTHER_TEST_KEY = b"PUBLIC-TEST-KEY-NOT-FOR-DEPLOYMENT-000002"


class KeyedCustodyAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(20261103)
        cls.stars = rng.normal(size=(2, 9, 180)) * 0.1
        cls.stars[:, 0, :] += (
            0.08 * np.maximum(np.arange(180, dtype=np.float64) - 69.0, 0.0)
        )

    def verifier(self, *, key=PUBLIC_FIXTURE_KEY):
        return KeyedCustodyVerifier(
            curves=2, stars_per_curve=9, session_id="example-session-A",
            instrument_id="declared-instrument-A",
            target_id="declared-target-A", clock_id="unverified-clock-A",
            key_id="public-key-label-A", verification_key=key,
        )

    def signed(self, k, *, previous="0" * 64, key=PUBLIC_FIXTURE_KEY,
               frame=None, **changes):
        values = self.stars[:, :, k] if frame is None else frame
        packet = AuthenticatedPacket(
            cadence_index=k, key_id="public-key-label-A",
            session_id="example-session-A",
            instrument_id="declared-instrument-A",
            target_id="declared-target-A", clock_id="unverified-clock-A",
            frame_shape=(2, 9),
            start_seconds=1000.0 + 2.0 * k,
            end_seconds=1000.5 + 2.0 * k,
            start_uncertainty_seconds=0.01, end_uncertainty_seconds=0.01,
            raw_frame_bytes=np.array(
                values, dtype="<f8", order="C", copy=True
            ).tobytes(order="C"),
            previous_mac_hex=previous, mac_hex="",
        )
        return seal_software_test_packet(
            replace(packet, **changes), public_fixture_key=key
        )

    def append_through(self, verifier, last):
        previous = "0" * 64
        packets = []
        for k in range(last + 1):
            packet = self.signed(k, previous=previous)
            verifier.append(packet)
            previous = packet.mac_hex
            packets.append(packet)
        return packets

    def test_rfc4231_case1_sha256_known_answer(self):
        expected = (
            "b0344c61d8db38535ca8afceaf0bf12b"
            "881dc200c9833da726e9376c2e32cff7"
        )
        self.assertEqual(
            hmac.new(b"\x0b" * 20, b"Hi There", hashlib.sha256).hexdigest(),
            expected,
        )

    def test_complete_valid_packets_preserve_all_prefix_diagnostics(self):
        verifier = self.verifier()
        previous = "0" * 64
        for k in range(180):
            packet = self.signed(k, previous=previous)
            verifier.append(packet)
            previous = packet.mac_hex
            if k in (81, 83, 179):
                output = verifier.score_latest()
                expected = score_observed_prefix(
                    self.stars[:, :, :k + 1], endpoint=k
                )
                for field in expected:
                    np.testing.assert_array_equal(output[field], expected[field])
        self.assertEqual(verifier.count, 180)
        self.assertEqual(len(verifier.packets), 180)
        self.assertFalse(verifier.blocked)
        self.assertEqual(verifier.verify_custody(), previous)
        self.assertEqual(verifier.packets[0].raw_frame_bytes,
                         self.signed(0).raw_frame_bytes)

    def test_byte_and_declared_metadata_changes_are_rejected_and_block(self):
        base = self.signed(0)
        flipped = bytearray(base.raw_frame_bytes)
        flipped[1] ^= 0x01
        attacks = [
            replace(base, raw_frame_bytes=bytes(flipped)),
            replace(base, start_seconds=base.start_seconds + 0.01),
            replace(base, target_id="other-target"),
            replace(base, clock_id="other-clock"),
            replace(base, instrument_id="other-instrument"),
            replace(base, key_id="other-key-id"),
            replace(base, session_id="other-session"),
            replace(base, mac_hex="0" * 64),
            replace(base, previous_mac_hex="a" * 64),
            replace(base, frame_shape=(1, 18)),
            replace(base, raw_frame_bytes=base.raw_frame_bytes[:-1]),
        ]
        for attacked in attacks:
            with self.subTest(attack=attacked):
                verifier = self.verifier()
                with self.assertRaises(ValueError):
                    verifier.append(attacked)
                self.assertTrue(verifier.blocked)
                self.assertEqual(verifier.count, 0)
                self.assertEqual(verifier.packets, ())
                with self.assertRaisesRegex(ValueError, "blocked"):
                    verifier.append(base)

    def test_wrong_shared_verification_key_does_not_accept_valid_packet(self):
        verifier = self.verifier(key=OTHER_TEST_KEY)
        with self.assertRaisesRegex(ValueError, "HMAC"):
            verifier.append(self.signed(0))
        self.assertTrue(verifier.blocked)
        self.assertEqual(verifier.count, 0)

    def test_mac_predecessor_prevents_partial_splice_or_reordered_packets(self):
        first = self.signed(0)
        second = self.signed(1, previous=first.mac_hex)
        for packet in (second, self.signed(2)):
            verifier = self.verifier()
            with self.subTest(index=packet.cadence_index):
                with self.assertRaises(ValueError):
                    verifier.append(packet)
                self.assertTrue(verifier.blocked)
                self.assertEqual(verifier.count, 0)
        verifier = self.verifier()
        verifier.append(first)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verifier.append(first)
        self.assertTrue(verifier.blocked)

    def test_changed_ordered_frame_or_time_produces_different_mac(self):
        original = self.signed(0)
        changed = self.stars[:, :, 0].copy()
        changed[0, 0] += 0.125
        different_frame = self.signed(0, frame=changed)
        different_time = self.signed(0, end_seconds=1000.6)
        self.assertNotEqual(original.mac_hex, different_frame.mac_hex)
        self.assertNotEqual(original.mac_hex, different_time.mac_hex)
        self.assertNotEqual(different_frame.mac_hex, different_time.mac_hex)

    def test_identical_signed_streams_yield_identical_packet_macs(self):
        first, second = self.verifier(), self.verifier()
        left = self.append_through(first, 3)
        right = self.append_through(second, 3)
        self.assertEqual(
            tuple(packet.mac_hex for packet in left),
            tuple(packet.mac_hex for packet in right),
        )
        self.assertEqual(first.verify_custody(), second.verify_custody())

    def test_mutation_cannot_change_signed_bytes(self):
        verifier = self.verifier()
        source = self.stars[:, :, 0].copy()
        signed = self.signed(0, frame=source)
        verifier.append(signed)
        source[:] = 999
        public_packets = verifier.packets
        self.assertIsInstance(public_packets, tuple)
        self.assertEqual(verifier.verify_custody(), signed.mac_hex)
        self.assertEqual(public_packets[0].raw_frame_bytes, signed.raw_frame_bytes)

    def test_key_possession_does_not_prove_sensor_truth(self):
        honest = self.verifier()
        forged = self.verifier()
        original = self.signed(0)
        arbitrary = np.full((2, 9), 123.5)
        falsified = self.signed(0, frame=arbitrary)
        honest.append(original)
        forged.append(falsified)
        self.assertFalse(honest.blocked)
        self.assertFalse(forged.blocked)
        self.assertNotEqual(honest.verify_custody(), forged.verify_custody())
        self.assertEqual(forged.packets[0].raw_frame_bytes,
                         falsified.raw_frame_bytes)
        # Both pass because the fixture signer knows the same public key.

    def test_complete_transcript_replay_to_new_session_is_not_prevented(self):
        initial = self.verifier()
        saved_packets = self.append_through(initial, 2)
        replayed = self.verifier()
        for packet in saved_packets:
            replayed.append(packet)
        self.assertEqual(initial.verify_custody(), replayed.verify_custody())
        # This is a documented threat, not evidence of anti-replay protection.

    def test_valid_mac_does_not_bypass_p07_exposure_constraints(self):
        packet = self.signed(0, end_seconds=1000.0)
        verifier = self.verifier()
        with self.assertRaisesRegex(ValueError, "P0.7"):
            verifier.append(packet)
        self.assertTrue(verifier.blocked)
        self.assertEqual(verifier.count, 0)

    def test_finite_frames_and_exact_binary_format_required(self):
        nan_frame = np.full((2, 9), np.nan)
        invalid_packets = (
            self.signed(0, frame=nan_frame),
            replace(self.signed(0), raw_frame_bytes=b""),
        )
        for packet in invalid_packets:
            verifier = self.verifier()
            with self.assertRaises(ValueError):
                verifier.append(packet)
            self.assertTrue(verifier.blocked)

    def test_constructor_rejects_bad_keys_labels_and_dimensions(self):
        kwargs = dict(
            curves=2, stars_per_curve=9, session_id="example-session-A",
            instrument_id="declared-instrument-A",
            target_id="declared-target-A", clock_id="unverified-clock-A",
            key_id="public-key-label-A", verification_key=PUBLIC_FIXTURE_KEY,
        )
        for variation in (
            {"verification_key": b"short"},
            {"verification_key": "not bytes"},
            {"key_id": ""},
            {"curves": 0},
            {"stars_per_curve": 1},
        ):
            with self.subTest(variation=variation):
                with self.assertRaises(ValueError):
                    KeyedCustodyVerifier(**{**kwargs, **variation})

    def test_custody_verifier_blocks_unexpected_record_change(self):
        verifier = self.verifier()
        self.append_through(verifier, 81)
        trusted = verifier.verify_custody()
        self.assertEqual(len(trusted), 64)
        # Deliberate white-box mutation of signed packet metadata.
        verifier._packets[0] = replace(
            verifier._packets[0], start_seconds=999.0
        )
        with self.assertRaisesRegex(ValueError, "MAC mismatch"):
            verifier.verify_custody()
        self.assertTrue(verifier.blocked)
        with self.assertRaisesRegex(ValueError, "blocked"):
            verifier.score_latest()

    def test_uses_constant_time_compare_and_no_archived_scorer(self):
        source = (ROOT / "experiments/M38B-R/keyed_custody.py").read_text()
        self.assertIn("hmac.compare_digest", source)
        self.assertNotIn("observable_candidate", source)
        self.assertNotIn("arara_m38b", source)
        self.assertNotIn("thresholds.json", source)


if __name__ == "__main__":
    unittest.main()
