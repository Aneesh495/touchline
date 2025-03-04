"""Stratified calibration reporting with sample sizes and limited support.

Calibration can be good overall yet poor within a subgroup (a competition, a shot
type, a game state). This module reports proper scores and calibration error per
stratum alongside the stratum's sample size, and flags strata too small to judge as
having limited support rather than reporting a confident but meaningless number.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from touchline.models.calibration import (
    brier_score,
    expected_calibration_error,
    log_loss,
)


@dataclass(frozen=True)
class StratumReport:
    name: str
    count: int
    log_loss: float
    brier: float
    ece: float
    limited_support: bool


def stratified_calibration(
    y: np.ndarray,
    p: np.ndarray,
    strata: list[str],
    min_support: int = 50,
) -> list[StratumReport]:
    """Report calibration per stratum.

    ``strata[i]`` is the subgroup label of example i. A stratum with fewer than
    ``min_support`` examples is marked ``limited_support`` and its metrics, while
    computed, should be read as indicative only.
    """
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    strata_arr = np.asarray(strata)
    reports: list[StratumReport] = []
    for name in sorted(set(strata)):
        mask = strata_arr == name
        n = int(mask.sum())
        if n == 0:
            continue
        ys, ps = y[mask], p[mask]
        reports.append(
            StratumReport(
                name=name,
                count=n,
                log_loss=log_loss(ys, ps) if n > 0 else float("nan"),
                brier=brier_score(ys, ps),
                ece=expected_calibration_error(ys, ps, bins=min(10, max(2, n // 10))),
                limited_support=n < min_support,
            )
        )
    return reports


def out_of_support(
    x: np.ndarray, train_min: np.ndarray, train_max: np.ndarray
) -> np.ndarray:
    """Flag rows with any feature outside the training feature ranges.

    A calibrator fit on the training support says nothing about inputs beyond it, so
    such rows should carry a visible limited-support status rather than a confident
    calibrated probability.
    """
    x = np.asarray(x, dtype=float)
    below = (x < train_min).any(axis=1)
    above = (x > train_max).any(axis=1)
    return below | above
