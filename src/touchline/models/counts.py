"""Count and distributional models for goals, shots, corners, cards, and fouls.

Match counts are overdispersed relative to a plain Poisson: the variance exceeds
the mean because team strength and game state vary. This module fits a
negative-binomial (Poisson-gamma) model by matching the first two moments, which
captures overdispersion with one extra parameter, and reports whether the data are
actually overdispersed so a plain Poisson is not used where it is wrong.

The target is a per-match count conditioned on simple context (home/away, a
strength proxy). The project owns the moment-matching fit; it uses only numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class NegativeBinomialCount:
    """A negative-binomial count model fit by method of moments.

    The NB has mean mu and variance mu + mu^2 / r. When the sample variance exceeds
    the mean the data are overdispersed and r is finite; when they are equal the
    model reduces to Poisson (r -> infinity), which is reported.
    """

    mu: float = 0.0
    r: float = float("inf")
    overdispersed: bool = False

    def fit(self, counts: np.ndarray) -> NegativeBinomialCount:
        c = np.asarray(counts, dtype=float)
        self.mu = float(c.mean())
        var = float(c.var(ddof=1)) if len(c) > 1 else self.mu
        if var > self.mu + 1e-9 and self.mu > 0:
            # var = mu + mu^2 / r  =>  r = mu^2 / (var - mu)
            self.r = self.mu**2 / (var - self.mu)
            self.overdispersed = True
        else:
            self.r = float("inf")
            self.overdispersed = False
        return self

    def pmf(self, k: int) -> float:
        """Probability of exactly k events."""
        from math import exp, lgamma, log

        if not np.isfinite(self.r):
            # Poisson limit
            return float(exp(k * log(self.mu + 1e-12) - self.mu - lgamma(k + 1)))
        r, mu = self.r, self.mu
        p = r / (r + mu)
        log_pmf = (
            lgamma(k + r)
            - lgamma(r)
            - lgamma(k + 1)
            + r * log(p)
            + k * log(1 - p)
        )
        return float(exp(log_pmf))

    def mean_variance(self) -> tuple[float, float]:
        var = self.mu if not np.isfinite(self.r) else self.mu + self.mu**2 / self.r
        return self.mu, var
