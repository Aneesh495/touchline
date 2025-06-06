"""Convert canonical domain objects to Arrow tables and persist as Parquet.

Each converter flattens a list of domain objects into a columnar Arrow table with
an explicit, stable schema. The schema is the contract: column names, types, and
units are fixed here so downstream queries and the DuckDB surface can rely on them.
Nullable columns use Arrow nulls rather than sentinel values, so a missing body part
is null, not an invented default.

The :class:`ArrowStore` writes partitions to ``<root>/<competition>/<season>/<name>.parquet``
and records a content hash per partition. A partition is written once; a second
write with the same bytes is a no-op, and with different bytes raises unless an
explicit version bump is requested, preserving immutability.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from touchline.domain.events import Event, Shot
from touchline.domain.match import Match


def matches_to_table(matches: list[Match]) -> pa.Table:
    """Flatten matches into a columnar table of match-level facts."""
    cols: dict[str, list] = {
        "match_id": [], "competition": [], "season": [], "home": [], "away": [],
        "home_reg": [], "away_reg": [], "home_et": [], "away_et": [],
        "home_so": [], "away_so": [], "result": [], "neutral": [],
    }
    for m in matches:
        cols["match_id"].append(m.match_id.value)
        cols["competition"].append(m.competition.code)
        cols["season"].append(m.season)
        cols["home"].append(m.home.name)
        cols["away"].append(m.away.name)
        cols["home_reg"].append(m.score.home_regulation)
        cols["away_reg"].append(m.score.away_regulation)
        cols["home_et"].append(m.score.home_extra)
        cols["away_et"].append(m.score.away_extra)
        cols["home_so"].append(m.score.home_shootout)
        cols["away_so"].append(m.score.away_shootout)
        cols["result"].append(m.score.result_char())
        cols["neutral"].append(m.venue.neutral)
    return pa.table(cols)


def events_to_table(events: list[Event], match_id: str) -> pa.Table:
    """Flatten events into a columnar table with canonical coordinates."""
    cols: dict[str, list] = {
        "match_id": [], "index": [], "period": [], "second": [], "added": [],
        "type": [], "team": [], "player": [], "x": [], "y": [],
        "end_x": [], "end_y": [], "possession_id": [],
    }
    for e in events:
        cols["match_id"].append(match_id)
        cols["index"].append(e.index)
        cols["period"].append(e.clock.period.value)
        cols["second"].append(e.clock.second)
        cols["added"].append(e.clock.added)
        cols["type"].append(e.type.value)
        cols["team"].append(e.team.value)
        cols["player"].append(e.player.value if e.player else None)
        cols["x"].append(e.location.x if e.location else None)
        cols["y"].append(e.location.y if e.location else None)
        cols["end_x"].append(e.end_location.x if e.end_location else None)
        cols["end_y"].append(e.end_location.y if e.end_location else None)
        cols["possession_id"].append(e.possession_id)
    return pa.table(cols)


def shots_to_table(shots: list[Shot], match_id: str) -> pa.Table:
    """Flatten shots into a columnar table with the xG-eligible fields."""
    cols: dict[str, list] = {
        "match_id": [], "event_index": [], "team": [], "player": [],
        "x": [], "y": [], "distance_m": [], "angle_rad": [], "body_part": [],
        "is_penalty": [], "is_shootout": [], "is_goal": [], "situation": [],
    }
    for s in shots:
        cols["match_id"].append(match_id)
        cols["event_index"].append(s.event_index)
        cols["team"].append(s.team.value)
        cols["player"].append(s.player.value if s.player else None)
        cols["x"].append(s.location.x)
        cols["y"].append(s.location.y)
        cols["distance_m"].append(s.location.distance_to_goal_m())
        cols["angle_rad"].append(s.location.shot_angle_rad())
        cols["body_part"].append(s.body_part.value)
        cols["is_penalty"].append(s.is_penalty)
        cols["is_shootout"].append(s.is_shootout)
        cols["is_goal"].append(s.is_goal)
        cols["situation"].append(s.situation)
    return pa.table(cols)


@dataclass
class ArrowStore:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _partition_path(self, competition: str, season: str, name: str) -> Path:
        return self.root / competition / season / f"{name}.parquet"

    def write(
        self, competition: str, season: str, name: str, table: pa.Table, allow_version: bool = False
    ) -> str:
        """Write a partition immutably; return its content hash.

        If a partition already exists with identical bytes, this is a no-op. If it
        exists with different bytes and ``allow_version`` is False, it raises, so an
        accidental mutation of a frozen input is caught.
        """
        path = self._partition_path(competition, season, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        buf = pa.BufferOutputStream()
        pq.write_table(table, buf)
        data = buf.getvalue().to_pybytes()
        sha = hashlib.sha256(data).hexdigest()
        if path.exists():
            existing = hashlib.sha256(path.read_bytes()).hexdigest()
            if existing == sha:
                return sha
            if not allow_version:
                raise ValueError(
                    f"partition {path} exists with different content; "
                    "pass allow_version to write a new version"
                )
            path = path.with_name(f"{name}.{sha[:8]}.parquet")
        path.write_bytes(data)
        return sha

    def read(self, competition: str, season: str, name: str) -> pa.Table:
        return pq.read_table(self._partition_path(competition, season, name))

    def exists(self, competition: str, season: str, name: str) -> bool:
        return self._partition_path(competition, season, name).exists()

    def partitions(self) -> list[Path]:
        return sorted(self.root.rglob("*.parquet"))
