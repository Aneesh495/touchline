"""Hierarchical shrinkage oracles."""

import numpy as np

from touchline.models.hierarchical import HierarchicalRateModel


def test_small_sample_shrinks_more_than_large():
    model = HierarchicalRateModel()
    keys = ["established", "cameo"]
    # established: 20 goals in 3000 minutes; cameo: 2 goals in 90 minutes
    counts = np.array([20.0, 2.0])
    exposure = np.array([3000.0, 90.0])
    ests = model.shrink(keys, counts, exposure)
    by_key = {e.key: e for e in ests}
    # The cameo has the higher raw rate but should shrink more toward the mean.
    assert by_key["cameo"].raw_rate > by_key["established"].raw_rate
    assert by_key["cameo"].shrinkage_weight < by_key["established"].shrinkage_weight


def test_large_exposure_trusts_own_rate():
    model = HierarchicalRateModel()
    rng = np.random.default_rng(0)
    n = 50
    true_rate = rng.uniform(0.1, 0.9, n)
    exposure = rng.uniform(2000, 4000, n)
    counts = rng.poisson(true_rate * exposure)
    ests = model.shrink([f"p{i}" for i in range(n)], counts, exposure)
    # With heavy exposure, shrunk rate stays close to raw rate.
    for e in ests:
        assert abs(e.shrunk_rate - e.raw_rate) < 0.1


def test_exposure_disclosed_on_every_estimate():
    model = HierarchicalRateModel()
    ests = model.shrink(["a"], np.array([5.0]), np.array([450.0]))
    assert ests[0].exposure == 450.0
