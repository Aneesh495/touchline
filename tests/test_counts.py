"""Negative-binomial count model oracles."""

import numpy as np

from touchline.models.counts import NegativeBinomialCount


def test_detects_overdispersion():
    rng = np.random.default_rng(0)
    # Overdispersed: a mixture of two Poissons has variance above its mean.
    a = rng.poisson(2.0, 2000)
    b = rng.poisson(8.0, 2000)
    mixed = np.concatenate([a, b])
    m = NegativeBinomialCount().fit(mixed)
    assert m.overdispersed
    _, var = m.mean_variance()
    assert var > m.mu


def test_poisson_limit_when_not_overdispersed():
    rng = np.random.default_rng(1)
    c = rng.poisson(3.0, 5000)
    m = NegativeBinomialCount().fit(c)
    # A clean Poisson sample should be at or near the Poisson limit.
    assert not m.overdispersed or m.r > 50


def test_pmf_sums_to_about_one():
    rng = np.random.default_rng(2)
    c = rng.poisson(2.5, 3000) + rng.poisson(1.0, 3000)
    m = NegativeBinomialCount().fit(c)
    total = sum(m.pmf(k) for k in range(0, 40))
    assert abs(total - 1.0) < 1e-3


def test_mean_matches_sample():
    c = np.array([0, 1, 2, 3, 4, 2, 1, 0, 3, 2], dtype=float)
    m = NegativeBinomialCount().fit(c)
    assert abs(m.mu - c.mean()) < 1e-9
