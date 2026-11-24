"""Exhaustive, exact checks for the two-observer audit model."""

from fractions import Fraction
from itertools import product
import unittest


def report_distribution(sky_event, shared_failure, report_error):
    """Enumerate latent failure propagation and binary report error."""
    masses = [Fraction(0), Fraction(0)]
    for copied, flipped in product((False, True), repeat=2):
        copy_mass = shared_failure if copied else 1 - shared_failure
        flip_mass = report_error if flipped else 1 - report_error
        ideal_report = sky_event or copied
        masses[int(ideal_report ^ flipped)] += copy_mass * flip_mass
    return masses


def minimum_error(sky, fault):
    """Evaluate all four deterministic policies with equal class weights."""
    return min(
        sum((fault if pick_sky else sky)[report]
            for report, pick_sky in enumerate(policy)) / 2
        for policy in product((False, True), repeat=2)
    )


class PeerAuditChecks(unittest.TestCase):
    def test_all_rational_grid_cases(self):
        for error_index, common_index in product(range(51), range(101)):
            error = Fraction(error_index, 100)
            common = Fraction(common_index, 100)
            sky = report_distribution(True, common, error)
            fault = report_distribution(False, common, error)
            self.assertEqual(sum(sky), 1)
            self.assertEqual(sum(fault), 1)
            self.assertTrue(all(0 <= mass <= 1 for mass in sky + fault))
            self.assertEqual(
                minimum_error(sky, fault),
                (1 - (1 - common) * (1 - 2 * error)) / 2,
                (error, common),
            )
            self.assertEqual(sky == fault, common == 1 or error == Fraction(1, 2))

    def test_perfect_peer_without_shared_fault(self):
        sky = report_distribution(True, Fraction(0), Fraction(0))
        fault = report_distribution(False, Fraction(0), Fraction(0))
        self.assertEqual(minimum_error(sky, fault), 0)

    def test_complete_agreement_can_be_uninformative(self):
        sky = report_distribution(True, Fraction(1), Fraction(0))
        fault = report_distribution(False, Fraction(1), Fraction(0))
        self.assertEqual(sky, [0, 1])
        self.assertEqual(sky, fault)
        self.assertEqual(minimum_error(sky, fault), Fraction(1, 2))

    def test_architecture_examples(self):
        error = Fraction(1, 10)
        for common, expected in (
            (Fraction(0), Fraction(1, 10)),
            (Fraction(1, 2), Fraction(3, 10)),
            (Fraction(9, 10), Fraction(23, 50)),
            (Fraction(1), Fraction(1, 2)),
        ):
            sky = report_distribution(True, common, error)
            fault = report_distribution(False, common, error)
            self.assertEqual(minimum_error(sky, fault), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
