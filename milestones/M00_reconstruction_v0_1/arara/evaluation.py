from __future__ import annotations

from dataclasses import dataclass
from typing import Callable
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

from .synthetic import SyntheticSample
from .detectors import housekeeping_instability

ScoreFn = Callable[[SyntheticSample], np.ndarray]


@dataclass
class EvalResult:
    auc: float
    ap: float
    threshold: float
    early_recall: float
    premature_rate: float
    late_recall: float
    fpr_pre_reference: float
    median_lead_min: float
    false_alert_episodes_per_field_hour: float
    quarantine_rate: float = 0.0


def pre_reference_max(sample: SyntheticSample, score: np.ndarray, baseline_end: int = 36) -> float:
    return float(np.max(score[baseline_end:sample.reference_idx]))


def calibrate_threshold(
    train: list[SyntheticSample],
    score_fn: ScoreFn,
    target_fpr: float,
    baseline_end: int = 36,
) -> float:
    vals = [pre_reference_max(s, score_fn(s), baseline_end) for s in train if s.kind != "event"]
    if not vals:
        raise ValueError("No non-events for threshold calibration")
    # Conservative finite-sample quantile: 'higher' never interpolates below an observed score.
    return float(np.quantile(vals, 1.0 - target_fpr, method="higher"))


def calibrate_health_threshold(train: list[SyntheticSample], nominal_quantile: float = 0.99) -> float:
    vals: list[float] = []
    for s in train:
        h = housekeeping_instability(s.housekeeping)
        vals.extend(h[~s.instrument_bad].tolist())
    return float(np.quantile(vals, nominal_quantile, method="higher"))


def _first_crossing(score: np.ndarray, threshold: float, start: int, stop: int, allowed: np.ndarray | None = None) -> int | None:
    idx = np.arange(start, stop)
    mask = score[start:stop] >= threshold
    if allowed is not None:
        mask &= allowed[start:stop]
    hits = idx[mask]
    return None if len(hits) == 0 else int(hits[0])


def _count_upcrossings(score: np.ndarray, threshold: float, start: int, allowed: np.ndarray | None = None) -> int:
    active = score >= threshold
    if allowed is not None:
        active &= allowed
    active[:start] = False
    prev = np.concatenate([[False], active[:-1]])
    return int(np.sum(active & ~prev))


def evaluate(
    train: list[SyntheticSample],
    test: list[SyntheticSample],
    score_fn: ScoreFn,
    target_fpr: float,
    use_health_gate: bool = False,
    baseline_end: int = 36,
) -> EvalResult:
    threshold = calibrate_threshold(train, score_fn, target_fpr, baseline_end)
    health_threshold = calibrate_health_threshold(train) if use_health_gate else None

    labels = np.array([1 if s.kind == "event" else 0 for s in test])
    max_scores = np.array([pre_reference_max(s, score_fn(s), baseline_end) for s in test])
    auc = float(roc_auc_score(labels, max_scores))
    ap = float(average_precision_score(labels, max_scores))

    n_event = sum(s.kind == "event" for s in test)
    n_non = len(test) - n_event
    early = premature = late = false_pre = quarantined = 0
    leads: list[float] = []
    false_episodes = 0
    non_hours = 0.0

    for s in test:
        score = score_fn(s)
        allowed = None
        if health_threshold is not None:
            h = housekeeping_instability(s.housekeeping)
            allowed = h <= health_threshold
            q = _first_crossing(score, threshold, baseline_end, s.reference_idx, allowed=~allowed)
            if q is not None:
                quarantined += 1

        first = _first_crossing(score, threshold, baseline_end, s.reference_idx, allowed)
        if s.kind == "event":
            if first is not None and first < s.onset_idx:
                premature += 1
            elif first is not None:
                early += 1
                leads.append((s.reference_idx - first) * s.cadence_s / 60.0)
            else:
                late_first = _first_crossing(score, threshold, s.reference_idx, len(score), allowed)
                if late_first is not None:
                    late += 1
        else:
            if first is not None:
                false_pre += 1
            false_episodes += _count_upcrossings(score, threshold, baseline_end, allowed)
            non_hours += (len(score) - baseline_end) * s.cadence_s / 3600.0

    return EvalResult(
        auc=auc,
        ap=ap,
        threshold=threshold,
        early_recall=early / n_event,
        premature_rate=premature / n_event,
        late_recall=late / n_event,
        fpr_pre_reference=false_pre / n_non,
        median_lead_min=float(np.median(leads)) if leads else float("nan"),
        false_alert_episodes_per_field_hour=false_episodes / non_hours if non_hours else float("nan"),
        quarantine_rate=quarantined / len(test),
    )


def evaluate_precomputed(
    train: list[SyntheticSample],
    test: list[SyntheticSample],
    train_scores: list[np.ndarray],
    test_scores: list[np.ndarray],
    target_fpr: float,
    use_health_gate: bool = False,
    baseline_end: int = 36,
) -> EvalResult:
    vals = [pre_reference_max(s, sc, baseline_end) for s, sc in zip(train, train_scores) if s.kind != "event"]
    threshold = float(np.quantile(vals, 1.0 - target_fpr, method="higher"))
    health_threshold = calibrate_health_threshold(train) if use_health_gate else None

    labels = np.array([1 if s.kind == "event" else 0 for s in test])
    max_scores = np.array([pre_reference_max(s, sc, baseline_end) for s, sc in zip(test, test_scores)])
    auc = float(roc_auc_score(labels, max_scores))
    ap = float(average_precision_score(labels, max_scores))

    n_event = sum(s.kind == "event" for s in test)
    n_non = len(test) - n_event
    early = premature = late = false_pre = quarantined = 0
    leads: list[float] = []
    false_episodes = 0
    non_hours = 0.0

    for s, score in zip(test, test_scores):
        allowed = None
        if health_threshold is not None:
            h = housekeeping_instability(s.housekeeping)
            allowed = h <= health_threshold
            q = _first_crossing(score, threshold, baseline_end, s.reference_idx, allowed=~allowed)
            if q is not None:
                quarantined += 1
        first = _first_crossing(score, threshold, baseline_end, s.reference_idx, allowed)
        if s.kind == "event":
            if first is not None and first < s.onset_idx:
                premature += 1
            elif first is not None:
                early += 1
                leads.append((s.reference_idx - first) * s.cadence_s / 60.0)
            else:
                late_first = _first_crossing(score, threshold, s.reference_idx, len(score), allowed)
                if late_first is not None:
                    late += 1
        else:
            if first is not None:
                false_pre += 1
            false_episodes += _count_upcrossings(score, threshold, baseline_end, allowed)
            non_hours += (len(score) - baseline_end) * s.cadence_s / 3600.0

    return EvalResult(
        auc=auc,
        ap=ap,
        threshold=threshold,
        early_recall=early / n_event,
        premature_rate=premature / n_event,
        late_recall=late / n_event,
        fpr_pre_reference=false_pre / n_non,
        median_lead_min=float(np.median(leads)) if leads else float("nan"),
        false_alert_episodes_per_field_hour=false_episodes / non_hours if non_hours else float("nan"),
        quarantine_rate=quarantined / len(test),
    )
