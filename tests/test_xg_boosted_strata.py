"""Boosted xG and stratified calibration oracles."""

import numpy as np
import pytest

from touchline.models.strata import out_of_support, stratified_calibration


def _xg_data(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    dist = rng.uniform(1, 35, n)
    angle = rng.uniform(0.05, 1.2, n)
    rest = np.zeros((n, 5))
    x = np.column_stack([dist, angle, rest])
    logit = 2.0 - 0.15 * dist + 1.6 * angle
    p = 1 / (1 + np.exp(-logit))
    y = (rng.uniform(size=n) < p).astype(float)
    return x, y


def test_boosted_xg_learns_distance_effect():
    lgb = pytest.importorskip("lightgbm")
    _ = lgb
    from touchline.models.xg_boosted import BoostedXG

    x, y = _xg_data()
    split = int(0.7 * len(y))
    val = int(0.85 * len(y))
    model = BoostedXG(n_estimators=200).fit(
        x[:split], y[:split], x[split:val], y[split:val]
    )
    close = model.predict_proba([[6, 1.0, 0, 0, 0, 0, 0]])[0]
    far = model.predict_proba([[30, 0.2, 0, 0, 0, 0, 0]])[0]
    assert close > far
    # early stopping chose a sensible iteration
    assert model.best_iteration >= 1


def test_stratified_calibration_reports_per_group_and_flags_small():
    rng = np.random.default_rng(1)
    n = 600
    y = (rng.uniform(size=n) < 0.3).astype(float)
    p = np.clip(rng.uniform(size=n), 0.01, 0.99)
    strata = ["EPL"] * 500 + ["UCL"] * 90 + ["tiny"] * 10
    reports = stratified_calibration(y, p, strata, min_support=50)
    by_name = {r.name: r for r in reports}
    assert by_name["EPL"].count == 500 and not by_name["EPL"].limited_support
    assert by_name["tiny"].count == 10 and by_name["tiny"].limited_support


def test_out_of_support_flags_extreme_rows():
    train = np.array([[0.0, 0.0], [10.0, 1.0]])
    tmin = train.min(axis=0)
    tmax = train.max(axis=0)
    rows = np.array([[5.0, 0.5], [20.0, 0.5], [-1.0, 0.5]])
    flags = out_of_support(rows, tmin, tmax)
    assert list(flags) == [False, True, True]
