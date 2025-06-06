"""DuckDB query surface over the Parquet partitions.

DuckDB reads Parquet directly, so we can run SQL over the columnar store without a
load step. This wrapper opens an in-memory DuckDB connection, registers a glob over
the store's Parquet files as views, and exposes a few typed convenience queries
(top scorers by shots, per-competition shot counts, goal rate by distance band)
plus a raw query escape hatch. It never mutates the store; it only reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb


@dataclass
class DuckQuery:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.con = duckdb.connect(database=":memory:")

    def _glob(self, name: str) -> str:
        return str(self.root / "**" / f"{name}.parquet")

    def shots(self):
        """A DuckDB relation over all shot partitions."""
        return self.con.read_parquet(self._glob("shots"), hive_partitioning=False)

    def shot_count_by_competition(self) -> list[tuple[str, int]]:
        rel = self.con.sql(
            f"SELECT match_id, count(*) AS n FROM read_parquet('{self._glob('shots')}') "
            "GROUP BY match_id"
        )
        return rel.fetchall()

    def goal_rate_by_distance_band(self, band_m: float = 5.0) -> list[tuple[int, float, int]]:
        """Observed goal rate by distance band, with the count per band.

        Returns (band_index, goal_rate, n) so a reliability-style view can be built
        directly from the store. Shootout kicks are excluded.
        """
        q = (
            f"SELECT CAST(distance_m / {band_m} AS INTEGER) AS band, "
            "avg(CAST(is_goal AS DOUBLE)) AS goal_rate, count(*) AS n "
            f"FROM read_parquet('{self._glob('shots')}') "
            "WHERE NOT is_shootout "
            "GROUP BY band ORDER BY band"
        )
        return self.con.sql(q).fetchall()

    def total_shots(self) -> int:
        rel = self.con.sql(
            f"SELECT count(*) AS n FROM read_parquet('{self._glob('shots')}')"
        )
        return int(rel.fetchall()[0][0])

    def query(self, sql: str):
        """Raw read-only query escape hatch."""
        return self.con.sql(sql)

    def close(self) -> None:
        self.con.close()
