"""Serving oracles: cache, bounds, batched inference, latency."""

import numpy as np
import pytest

from touchline.data.sample import generate_sample_shots
from touchline.models.xg_logistic import LogisticXG
from touchline.serving.cache import LRUCache
from touchline.serving.inference import (
    BatchInferenceService,
    BoundsExceeded,
    InferenceBounds,
)


def test_lru_evicts_least_recently_used():
    c: LRUCache = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1  # a now most recent
    c.put("c", 3)  # evicts b
    assert c.get("b") is None
    assert c.get("a") == 1
    assert c.get("c") == 3


def test_service_caches_repeated_shots():
    x, y, _ = generate_sample_shots(n=2000, seed=0)
    model = LogisticXG(epochs=100).fit(x, y)
    svc = BatchInferenceService(model.predict_proba)
    batch = x[:10]
    svc.predict_shots(batch)
    hits_before = svc.cache.hits
    svc.predict_shots(batch)  # identical rows -> cache hits
    assert svc.cache.hits > hits_before


def test_service_rejects_oversize_batch():
    model = LogisticXG(epochs=10).fit(*generate_sample_shots(n=500)[:2])
    svc = BatchInferenceService(model.predict_proba, bounds=InferenceBounds(max_batch=4))
    with pytest.raises(BoundsExceeded):
        svc.predict_shots(np.zeros((5, 7)))


def test_service_rejects_oversize_sequence():
    def seq_predict(seqs):
        return [np.zeros(len(s)) for s in seqs]

    svc = BatchInferenceService(
        lambda f: np.zeros(len(f)),
        seq_predict=seq_predict,
        bounds=InferenceBounds(max_seq_len=5),
    )
    with pytest.raises(BoundsExceeded):
        svc.predict_sequences([np.zeros((6, 8))])


def test_p95_latency_is_measured_and_finite():
    x, y, _ = generate_sample_shots(n=3000, seed=1)
    model = LogisticXG(epochs=100).fit(x, y)
    svc = BatchInferenceService(model.predict_proba, bounds=InferenceBounds(max_batch=256))
    rng = np.random.default_rng(2)

    def make_batch():
        idx = rng.integers(0, len(x), 128)
        return x[idx]

    p95 = svc.measure_p95_ms(make_batch, n_trials=20)
    assert p95 >= 0.0
    # The logistic model on 128 shots is trivially fast on CPU.
    assert p95 < 250.0
