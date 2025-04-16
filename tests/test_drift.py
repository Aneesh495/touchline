"""Drift monitoring oracles."""

import numpy as np

from touchline.monitoring.drift import (
    build_drift_report,
    calibration_drift,
    population_stability_index,
)


def test_psi_near_zero_for_same_distribution():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 5000)
    b = rng.normal(0, 1, 5000)
    assert population_stability_index(a, b) < 0.1


def test_psi_large_for_shifted_distribution():
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, 5000)
    b = rng.normal(3, 1, 5000)  # big mean shift
    assert population_stability_index(a, b) > 0.25


def test_calibration_drift_sign():
    y = np.array([0, 0, 1, 1])
    over = np.array([0.9, 0.9, 0.9, 0.9])  # over-predicting
    under = np.array([0.1, 0.1, 0.1, 0.1])  # under-predicting
    assert calibration_drift(y, over) > 0
    assert calibration_drift(y, under) < 0


def test_drift_report_flags_degradation():
    rng = np.random.default_rng(2)
    ref = {"dist": rng.normal(0, 1, 3000)}
    cur = {"dist": rng.normal(4, 1, 3000)}
    y = np.array([0, 1, 0, 1, 0])
    p = np.array([0.9, 0.9, 0.9, 0.9, 0.9])  # badly over-confident
    report = build_drift_report(ref, cur, y, p)
    assert "dist" in report.drifted_features()
    assert report.calibration_degraded
