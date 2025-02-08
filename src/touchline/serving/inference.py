"""Batched CPU inference service.

The service holds a fitted shot model and an optional sequence model and answers
batched requests. It enforces bounds: a maximum batch size and a maximum sequence
length, rejecting over-large requests rather than silently truncating in a way
that would change results. Results for repeated shot feature vectors are cached.

Latency is measured with a monotonic clock around the model call so the p95 figure
reflects actual compute, and a helper computes the p95 over a set of batches for
the serving gate.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from touchline.serving.cache import LRUCache


class BoundsExceeded(ValueError):
    pass


@dataclass(frozen=True)
class InferenceBounds:
    max_batch: int = 256
    max_seq_len: int = 40


class BatchInferenceService:
    """Serve shot xG and (optionally) possession-sequence predictions.

    ``shot_predict`` maps an (N, F) feature array to N probabilities.
    ``seq_predict`` maps a list of (L, F) arrays to a list of per-step predictions.
    Both are plain callables so any fitted model (logistic, neural) can be served.
    """

    def __init__(
        self,
        shot_predict: Callable[[np.ndarray], np.ndarray],
        seq_predict: Optional[Callable[[list], list]] = None,
        bounds: InferenceBounds | None = None,
        cache_capacity: int = 4096,
    ):
        self.shot_predict = shot_predict
        self.seq_predict = seq_predict
        self.bounds = bounds or InferenceBounds()
        self.cache: LRUCache = LRUCache(cache_capacity)
        self.last_latency_s: float = 0.0

    def predict_shots(self, features: np.ndarray) -> np.ndarray:
        features = np.asarray(features, dtype=float)
        if features.ndim != 2:
            raise ValueError("features must be 2-D (N, F)")
        n = features.shape[0]
        if n > self.bounds.max_batch:
            raise BoundsExceeded(
                f"batch {n} exceeds max_batch {self.bounds.max_batch}"
            )
        out = np.empty(n, dtype=float)
        uncached_rows = []
        uncached_idx = []
        for i in range(n):
            key = features[i].tobytes()
            cached = self.cache.get(key)
            if cached is not None:
                out[i] = cached
            else:
                uncached_rows.append(features[i])
                uncached_idx.append(i)
        t0 = time.monotonic()
        if uncached_rows:
            preds = self.shot_predict(np.vstack(uncached_rows))
            for j, i in enumerate(uncached_idx):
                out[i] = float(preds[j])
                self.cache.put(features[i].tobytes(), out[i])
        self.last_latency_s = time.monotonic() - t0
        return out

    def predict_sequences(self, seqs: list[np.ndarray]) -> list[np.ndarray]:
        if self.seq_predict is None:
            raise RuntimeError("no sequence model configured")
        for s in seqs:
            if len(s) > self.bounds.max_seq_len:
                raise BoundsExceeded(
                    f"sequence length {len(s)} exceeds max {self.bounds.max_seq_len}"
                )
        t0 = time.monotonic()
        out = self.seq_predict(seqs)
        self.last_latency_s = time.monotonic() - t0
        return out

    def measure_p95_ms(
        self, make_batch: Callable[[], np.ndarray], n_trials: int = 30
    ) -> float:
        """Run ``n_trials`` shot batches and return the p95 latency in ms.

        The cache is bypassed for the measurement by using fresh random batches so
        the figure reflects real compute, not cache hits.
        """
        latencies = []
        for _ in range(n_trials):
            batch = make_batch()
            self.cache = LRUCache(self.cache.capacity)  # clear to avoid cache hits
            self.predict_shots(batch)
            latencies.append(self.last_latency_s * 1000.0)
        latencies.sort()
        idx = min(len(latencies) - 1, int(0.95 * len(latencies)))
        return latencies[idx]
