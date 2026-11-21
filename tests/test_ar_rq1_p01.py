"""Regression tests for the AR-RQ1-P01 preregistered synthetic generator."""

import numpy as np
import pytest

from scripts.ar_rq1_p01 import (
    EPOCH_COUNT,
    EVENT_DEPTH,
    EVENT_SLICE,
    REFERENCE_COUNT,
    SCENARIOS,
    ESTIMATORS,
    correct,
    generate_trial,
    window_depth,
)


def test_generator_is_deterministic_and_seeds_differ():
    a = generate_trial(0, "SHARED")
    b = generate_trial(0, "SHARED")
    c = generate_trial(1, "SHARED")
    assert all(np.array_equal(x, y) for x, y in zip(a, b))
    assert not np.array_equal(a[1], c[1])


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_event_pair_differs_only_at_declared_epochs(scenario):
    target_event, target_null, refs = generate_trial(3, scenario)
    assert target_event.shape == target_null.shape == (EPOCH_COUNT,)
    assert refs.shape == (REFERENCE_COUNT, EPOCH_COUNT)
    expected = np.zeros(EPOCH_COUNT)
    expected[EVENT_SLICE] = EVENT_DEPTH
    np.testing.assert_allclose(target_event - target_null, expected, atol=1e-14)


def test_scenarios_share_noise_and_only_change_intended_channels():
    shared_event, shared_null, shared_refs = generate_trial(5, "SHARED")
    ref_event, ref_null, corrupted_refs = generate_trial(5, "REF_CONTAM")
    _, local_null, local_refs = generate_trial(5, "TARGET_ARTIFACT")
    np.testing.assert_array_equal(shared_null, ref_null)
    np.testing.assert_array_equal(shared_event, ref_event)
    np.testing.assert_array_equal(shared_refs, local_refs)
    np.testing.assert_array_equal(shared_null[:128], local_null[:128])
    np.testing.assert_array_equal(shared_null[136:], local_null[136:])
    np.testing.assert_allclose(
        local_null[EVENT_SLICE] - shared_null[EVENT_SLICE], -0.02, atol=1e-14
    )
    diff = corrupted_refs - shared_refs
    np.testing.assert_allclose(diff[:, :128], 0.0, atol=0.0)
    np.testing.assert_allclose(diff[:, 136:], 0.0, atol=0.0)
    assert np.count_nonzero(np.abs(diff[:, 128]) > 0.01) == 12


@pytest.mark.parametrize("estimator", ESTIMATORS)
def test_reference_correction_does_not_suppress_additive_event(estimator):
    event, null, references = generate_trial(9, "REF_CONTAM")
    event_curve = correct(event, references, estimator)
    null_curve = correct(null, references, estimator)
    np.testing.assert_allclose(event_curve - null_curve, event - null, atol=1e-14)
    ratio = (window_depth(event_curve) - window_depth(null_curve)) / EVENT_DEPTH
    assert abs(ratio - 1.0) < 1e-10


def test_reference_correction_does_not_mutate_inputs():
    event, _, references = generate_trial(10, "SHARED")
    event_before = event.copy()
    references_before = references.copy()
    for estimator in ESTIMATORS:
        corrected = correct(event, references, estimator)
        assert corrected.shape == event.shape
    np.testing.assert_array_equal(event, event_before)
    np.testing.assert_array_equal(references, references_before)


@pytest.mark.parametrize("estimator", ("MEAN_REF", "MEDIAN_REF"))
def test_reference_estimators_match_independent_pointwise_oracle(estimator):
    event, _, references = generate_trial(0, "REF_CONTAM")
    measured = correct(event, references, estimator)
    oracle = np.empty(EPOCH_COUNT)
    for epoch in range(EPOCH_COUNT):
        values = sorted(float(x) for x in references[:, epoch])
        reference = (
            sum(values) / REFERENCE_COUNT
            if estimator == "MEAN_REF"
            else values[REFERENCE_COUNT // 2]
        )
        oracle[epoch] = event[epoch] - reference
    np.testing.assert_allclose(measured, oracle, atol=1e-14)


def test_reject_out_of_contract_inputs():
    with pytest.raises(ValueError):
        generate_trial(-1, "SHARED")
    with pytest.raises(ValueError):
        generate_trial(0, "unknown")
    event, _, references = generate_trial(0, "SHARED")
    with pytest.raises(ValueError):
        correct(event, references, "unknown")
    with pytest.raises(ValueError):
        correct(event[:-1], references, "RAW")
