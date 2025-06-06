"""Arrow/Parquet store and DuckDB query oracles."""

import pytest

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import BodyPart, Event, EventType, Shot
from touchline.domain.geometry import Point
from touchline.domain.identifiers import Provider, TeamId
from touchline.store.arrow_store import (
    ArrowStore,
    events_to_table,
    shots_to_table,
)
from touchline.store.duck import DuckQuery

A = TeamId(Provider.STATSBOMB, "A")


def _events():
    return [
        Event(0, MatchClock(PeriodKind.FIRST_HALF, 60), EventType.PASS, A, None, Point(0.3, 0.5)),
        Event(1, MatchClock(PeriodKind.FIRST_HALF, 65), EventType.SHOT, A, None, Point(0.9, 0.5)),
    ]


def _shots(goal_flags):
    out = []
    for i, (x, goal) in enumerate(goal_flags):
        out.append(
            Shot(i, MatchClock(PeriodKind.FIRST_HALF, i), A, None, Point(x, 0.5),
                 BodyPart.RIGHT_FOOT, False, False, goal)
        )
    return out


def test_events_table_schema_and_nulls():
    t = events_to_table(_events(), "m1")
    assert set(["match_id", "index", "type", "x", "y"]).issubset(t.column_names)
    assert t.num_rows == 2
    # player column is null (no player set)
    assert t.column("player").to_pylist() == [None, None]


def test_store_write_is_immutable(tmp_path):
    store = ArrowStore(tmp_path)
    t = shots_to_table(_shots([(0.9, True), (0.6, False)]), "m1")
    sha1 = store.write("LALIGA", "2020-2021", "shots", t)
    # identical rewrite is a no-op returning the same hash
    sha2 = store.write("LALIGA", "2020-2021", "shots", t)
    assert sha1 == sha2
    # different content without a version bump raises
    t2 = shots_to_table(_shots([(0.9, True)]), "m1")
    with pytest.raises(ValueError):
        store.write("LALIGA", "2020-2021", "shots", t2)


def test_duckdb_queries_over_store(tmp_path):
    store = ArrowStore(tmp_path)
    # close shots score, far shots mostly miss
    shots = _shots([(0.97, True), (0.95, True), (0.5, False), (0.45, False)])
    store.write("LALIGA", "2020-2021", "shots", shots_to_table(shots, "m1"))
    dq = DuckQuery(tmp_path)
    assert dq.total_shots() == 4
    bands = dq.goal_rate_by_distance_band(band_m=10.0)
    # closest band should have a higher goal rate than the farthest
    assert bands[0][1] >= bands[-1][1]
    dq.close()
