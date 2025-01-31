"""Hierarchical player/role/club effects with shrinkage and exposure.

Raw per-player rates are noisy: a striker with two goals in ninety minutes has a
higher raw rate than one with twenty in three thousand, yet we should not rank the
first above the second. A hierarchical (partial-pooling) estimate shrinks each
player's rate toward the group mean by an amount that depends on their exposure,
so small samples are pulled strongly toward the prior and large samples are
trusted.

This implements an empirical-Bayes shrinkage for a rate (events per unit
exposure, e.g. goals per 90). The population mean and variance are estimated from
the data, and each player's posterior mean is a precision-weighted average of
their own rate and the population mean. Exposure (minutes) is carried alongside so
any ranking can disclose the sample behind each estimate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ShrunkEstimate:
    key: str
    raw_rate: float
    shrunk_rate: float
    exposure: float
    shrinkage_weight: float  # 0 = fully prior, 1 = fully own data


@dataclass
class HierarchicalRateModel:
    """Empirical-Bayes shrinkage of per-entity rates toward a population mean."""

    prior_mean: float = 0.0
    prior_var: float = 0.0
    fitted: bool = False

    def fit(self, counts: np.ndarray, exposure: np.ndarray) -> HierarchicalRateModel:
        counts = np.asarray(counts, dtype=float)
        exposure = np.asarray(exposure, dtype=float)
        rates = np.divide(
            counts, exposure, out=np.zeros_like(counts), where=exposure > 0
        )
        # Exposure-weighted population mean.
        total_exp = exposure.sum()
        self.prior_mean = float((counts.sum() / total_exp) if total_exp > 0 else 0.0)
        # Between-entity variance of rates, exposure weighted, floored at zero.
        if total_exp > 0:
            w = exposure / total_exp
            var = float((w * (rates - self.prior_mean) ** 2).sum())
            # subtract the expected within-entity (Poisson) variance component
            mean_within = float(
                (w * np.divide(self.prior_mean, exposure, out=np.zeros_like(exposure), where=exposure > 0)).sum()
            )
            self.prior_var = max(var - mean_within, 1e-9)
        else:
            self.prior_var = 1e-9
        self.fitted = True
        return self

    def shrink(
        self, keys: list[str], counts: np.ndarray, exposure: np.ndarray
    ) -> list[ShrunkEstimate]:
        if not self.fitted:
            self.fit(counts, exposure)
        counts = np.asarray(counts, dtype=float)
        exposure = np.asarray(exposure, dtype=float)
        out: list[ShrunkEstimate] = []
        for k, c, e in zip(keys, counts, exposure, strict=True):
            raw = c / e if e > 0 else 0.0
            # Within-entity variance of the rate estimate ~ prior_mean / exposure
            # (Poisson). Shrinkage weight is prior_var / (prior_var + within_var).
            within_var = (self.prior_mean / e) if e > 0 else np.inf
            w = self.prior_var / (self.prior_var + within_var) if np.isfinite(within_var) else 0.0
            shrunk = w * raw + (1 - w) * self.prior_mean
            out.append(
                ShrunkEstimate(
                    key=k,
                    raw_rate=raw,
                    shrunk_rate=shrunk,
                    exposure=e,
                    shrinkage_weight=w,
                )
            )
        return out
