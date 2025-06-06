"""Columnar persistence for canonical data using Arrow, Parquet, and DuckDB.

The architecture names Arrow/Parquet/DuckDB as the storage substrate. This layer
turns canonical domain objects into immutable, partitioned Arrow/Parquet tables and
exposes a DuckDB query surface over them, so analysis runs on columnar data rather
than re-parsing provider JSON every time.

Partitioning is by competition and season, matching the coverage matrix, so a query
can prune to the relevant partitions. Writes are immutable: a partition is written
once with a content hash, and a rewrite with different bytes is a new version rather
than an in-place mutation, preserving the frozen-input guarantee the evaluation
protocol depends on.
"""

from touchline.store.arrow_store import (
    ArrowStore,
    events_to_table,
    matches_to_table,
    shots_to_table,
)
from touchline.store.duck import DuckQuery

__all__ = [
    "ArrowStore",
    "events_to_table",
    "matches_to_table",
    "shots_to_table",
    "DuckQuery",
]
