
from pathlib import Path
import sys

import numpy as np
from scipy.stats import linregress

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))

import arara_m4 as m4
import arara_m2 as m2
import arara_m3 as m3


def test_template_end_values_match_levels():
    cfg = m4.Config()
    bank = m4.build_template_bank(cfg)
    for meta in bank["metadata"]:
        assert np.isclose(
            meta["end_value"],
            meta["level"],
            atol=1e-10,
        )


def test_template_bank_has_no_deduplication_keys_repeated():
    cfg = m4.Config()
    bank = m4.build_template_bank(cfg)
    keys = []
    for length, group in bank["groups"].items():
        for row in group["matrix"]:
            keys.append(
                (length, tuple(np.round(row, 12)))
            )
    assert len(keys) == len(set(keys))
    assert bank["retained_count"] == len(keys)


def test_template_vectors_are_centered_and_unit_norm():
    bank = m4.build_template_bank(m4.Config())
    for group in bank["groups"].values():
        assert np.allclose(
            group["matrix"].mean(axis=1), 0.0
        )
        assert np.allclose(
            np.linalg.norm(
                group["matrix"], axis=1
            ),
            1.0,
        )


def test_matched_filter_exact_template_scores_high():
    cfg = m4.Config()
    bank = m4.build_template_bank(cfg)
    meta = bank["metadata"][0]
    length = meta["length"]
    group = bank["groups"][length]
    position = int(
        np.where(group["ids"] == meta["template_id"])[0][0]
    )
    unit = group["matrix"][position]

    # Adding any intercept and positive amplitude should preserve
    # correlation one with the centered template.
    series = np.zeros((1, 80))
    series[0, 20:20 + length] = 3.0 + 5.0 * unit
    score, winner = m4.matched_filter_score(
        series, bank
    )
    end = 20 + length - 1
    assert np.isinf(score[0, end])
    assert winner[0, end] == meta["template_id"]


def test_negative_template_direction_does_not_trigger_same_template():
    cfg = m4.Config()
    bank = m4.build_template_bank(cfg)
    meta = bank["metadata"][0]
    length = meta["length"]
    group = bank["groups"][length]
    position = int(
        np.where(group["ids"] == meta["template_id"])[0][0]
    )
    unit = group["matrix"][position]

    series = np.zeros((1, length))
    series[0] = -unit
    score, _ = m4.matched_filter_score(
        series, bank
    )
    assert score[0, -1] == 0.0


def test_correlation_t_equals_regression_t():
    rng = np.random.default_rng(11)
    x = np.linspace(0, 1, 20) ** 2
    y = 1.2 + 2.5 * x + rng.normal(0, 0.2, 20)

    xc = x - x.mean()
    yc = y - y.mean()
    corr = np.dot(xc, yc) / (
        np.linalg.norm(xc) * np.linalg.norm(yc)
    )
    t_corr = corr * np.sqrt(
        (len(x) - 2) / (1 - corr**2)
    )
    regression = linregress(x, y)
    t_reg = regression.slope / regression.stderr
    assert np.isclose(t_corr, t_reg)


def test_matched_filter_is_causal():
    cfg = m4.Config()
    bank = m4.build_template_bank(cfg)
    rng = np.random.default_rng(12)
    z = rng.normal(size=(2, 120))
    s1, w1 = m4.matched_filter_score(z, bank)

    z2 = z.copy()
    z2[:, 90:] += 1000
    s2, w2 = m4.matched_filter_score(z2, bank)
    assert np.allclose(s1[:, :90], s2[:, :90])
    assert np.array_equal(w1[:, :90], w2[:, :90])


def test_sbw_preprocessing_dependency_is_causal():
    cfg = m4.Config().data_config()
    rng = np.random.default_rng(13)
    y = rng.normal(
        size=(3, 1 + cfg.n_references, cfg.n_time)
    )
    r1, _, b1 = m3.normalize_sbw(y, cfg)

    y2 = y.copy()
    y2[:, :, cfg.baseline_n:] += 10000
    r2, _, b2 = m3.normalize_sbw(y2, cfg)
    assert np.allclose(b1, b2)
    assert np.allclose(
        r1[:, :cfg.baseline_n],
        r2[:, :cfg.baseline_n],
    )


def test_clopper_pearson_lower_boundaries():
    assert m4.clopper_pearson_lower(0, 100) == 0.0
    assert 0.9 < m4.clopper_pearson_lower(100, 100) < 1.0


def test_float32_threshold_contract():
    maxima = {
        "x": np.array(
            [5, 5, 5, 4, 3, 2, 1],
            dtype=np.float32,
        )
    }
    threshold, _, allowed = m2.conservative_threshold(
        maxima, 2 / 7
    )
    alerts = int(np.sum(maxima["x"] >= threshold))
    assert allowed["x"] == 2
    assert alerts <= 2
