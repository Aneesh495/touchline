"""Proper scoring rules and validation-only probability calibration.

Calibration asks whether predicted probabilities match observed frequencies: of
the shots assigned xG near 0.2, about 20% should be goals. We report the standard
proper scores (log loss and Brier score) and a reliability table that bins
predictions and compares mean prediction to observed rate per bin.

Calibrators are fit on a validation split only, never on training or test data,
so a reported test calibration is honest. Platt scaling fits a one-dimensional
logistic map from raw scores to calibrated probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def log_loss(y: np.ndarray, p: np.ndarray, eps: float = 1e-12) -> float:
    y = np.asarray(y, dtype=float)
    p = np.clip(np.asarray(p, dtype=float), eps, 1 - eps)
    return float(np.mean(-(y * np.log(p) + (1 - y) * np.log(1 - p))))


def brier_score(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    return float(np.mean((p - y) ** 2))


@dataclass(frozen=True)
class ReliabilityBin:
    low: float
    high: float
    count: int
    mean_prediction: float
    observed_rate: float


def reliability_table(y: np.ndarray, p: np.ndarray, bins: int = 10) -> list[ReliabilityBin]:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    out: list[ReliabilityBin] = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (p >= lo) & (p < hi if i < bins - 1 else p <= hi)
        count = int(mask.sum())
        if count == 0:
            out.append(ReliabilityBin(lo, hi, 0, float("nan"), float("nan")))
            continue
        out.append(
            ReliabilityBin(
                lo,
                hi,
                count,
                float(p[mask].mean()),
                float(y[mask].mean()),
            )
        )
    return out


def expected_calibration_error(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """Weighted average absolute gap between predicted and observed per bin."""
    table = reliability_table(y, p, bins)
    n = len(y)
    ece = 0.0
    for b in table:
        if b.count == 0:
            continue
        ece += (b.count / n) * abs(b.mean_prediction - b.observed_rate)
    return float(ece)


@dataclass
class PlattCalibrator:
    """One-dimensional logistic calibration of raw probabilities.

    Fit on validation data only. It maps a raw probability ``p`` through its logit
    and a learned affine transform back through a sigmoid, correcting systematic
    over- or under-confidence without touching the model.
    """

    a: float = 1.0
    b: float = 0.0
    lr: float = 0.1
    epochs: int = 500
    _fitted: bool = field(default=False, init=False)

    def fit(self, p_raw: np.ndarray, y: np.ndarray) -> PlattCalibrator:
        p = np.clip(np.asarray(p_raw, dtype=float), 1e-6, 1 - 1e-6)
        z = np.log(p / (1 - p))
        y = np.asarray(y, dtype=float)
        a, b = 1.0, 0.0
        for _ in range(self.epochs):
            pred = 1.0 / (1.0 + np.exp(-(a * z + b)))
            err = pred - y
            grad_a = float(np.mean(err * z))
            grad_b = float(np.mean(err))
            a -= self.lr * grad_a
            b -= self.lr * grad_b
        self.a, self.b = a, b
        self._fitted = True
        return self

    def transform(self, p_raw: np.ndarray) -> np.ndarray:
        p = np.clip(np.asarray(p_raw, dtype=float), 1e-6, 1 - 1e-6)
        z = np.log(p / (1 - p))
        return 1.0 / (1.0 + np.exp(-(self.a * z + self.b)))
