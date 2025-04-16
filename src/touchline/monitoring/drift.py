"""Input and calibration drift metrics.

The population stability index (PSI) measures how much a feature's distribution has
shifted between a reference period and a current period; a large PSI flags input
drift. Calibration drift tracks whether the model's reliability has degraded by
comparing the mean predicted probability to the observed rate over a window. Both
use only data within the declared window, so a later revision never leaks into an
earlier judgement.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def population_stability_index(
    reference: np.ndarray, current: np.ndarray, bins: int = 10
) -> float:
    """PSI between a reference and current sample of a single feature.

    Values are bucketed by the reference quantiles. PSI below 0.1 is stable, 0.1 to
    0.25 is moderate drift, and above 0.25 is significant drift (the usual rule of
    thumb). A small epsilon avoids log of zero in empty buckets.
    """
    ref = np.asarray(reference, dtype=float)
    cur = np.asarray(current, dtype=float)
    edges = np.quantile(ref, np.linspace(0, 1, bins + 1))
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_hist = np.histogram(ref, bins=edges)[0] / max(len(ref), 1)
    cur_hist = np.histogram(cur, bins=edges)[0] / max(len(cur), 1)
    eps = 1e-6
    ref_hist = np.clip(ref_hist, eps, None)
    cur_hist = np.clip(cur_hist, eps, None)
    return float(np.sum((cur_hist - ref_hist) * np.log(cur_hist / ref_hist)))


@dataclass(frozen=True)
class DriftReport:
    feature_psi: dict[str, float]
    calibration_gap: float  # mean predicted minus observed in the current window

    def drifted_features(self, threshold: float = 0.25) -> list[str]:
        return [f for f, v in self.feature_psi.items() if v > threshold]

    @property
    def calibration_degraded(self) -> bool:
        return abs(self.calibration_gap) > 0.05


def calibration_drift(y: np.ndarray, p: np.ndarray) -> float:
    """Mean predicted probability minus observed rate in a window.

    A positive value means the model is over-predicting (too confident), a negative
    value under-predicting. Near zero means calibration is holding.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if len(y) == 0:
        return 0.0
    return float(p.mean() - y.mean())


def build_drift_report(
    reference_features: dict[str, np.ndarray],
    current_features: dict[str, np.ndarray],
    y_current: np.ndarray,
    p_current: np.ndarray,
) -> DriftReport:
    psi = {
        name: population_stability_index(reference_features[name], current_features[name])
        for name in reference_features
        if name in current_features
    }
    gap = calibration_drift(y_current, p_current)
    return DriftReport(psi, gap)
