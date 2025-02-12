"""Serving: batched CPU inference and batch simulation with bounded resources.

The serving path loads models from the registry and answers inference requests in
batches, with an LRU cache for repeated inputs and explicit bounds on batch size
and sequence length. It never calls an external prediction service; all outputs
come from the local models. The batched inference is designed so a p95 latency
budget can be measured honestly on a pinned CPU host.
"""

from touchline.serving.cache import LRUCache
from touchline.serving.inference import (
    BatchInferenceService,
    InferenceBounds,
)

__all__ = ["BatchInferenceService", "InferenceBounds", "LRUCache"]
