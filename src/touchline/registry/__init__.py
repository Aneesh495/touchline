"""Model and artifact registry with versioning and atomic persistence.

A trained model is useless without the record of how it came to be: the dataset
version it was fit on, the feature contract, the calibration method, the fields it
is allowed to consume, the selection decision, and the exact checkpoint bytes. The
registry stores all of this as an immutable, checksummed record so a later run (or
an independent verifier) can reload the exact model and know what it is entitled
to do.

Persistence is atomic: a record is written to a temporary path and moved into
place, so an interrupted write never leaves a half-written record that a resumed
run would mistake for complete.
"""

from touchline.registry.artifacts import (
    ArtifactStore,
    AtomicWriteError,
    atomic_write_bytes,
)
from touchline.registry.model_card import ModelCard, ModelRegistry

__all__ = [
    "ArtifactStore",
    "AtomicWriteError",
    "atomic_write_bytes",
    "ModelCard",
    "ModelRegistry",
]
