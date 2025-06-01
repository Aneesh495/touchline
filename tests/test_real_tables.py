"""Real league-table reproduction tests (skip when results not cached).

These verify the rules engine reproduces known historical champions from real
cached football-data.co.uk results. They skip cleanly offline.
"""

from pathlib import Path

import pytest

from touchline.analysis.tables import reproduce_table

CACHE = Path("data/raw/cache")


def _cached(key: str) -> bool:
    import json

    idx = CACHE / "index.json"
    if not idx.exists():
        return False
    return key in json.loads(idx.read_text())


@pytest.mark.skipif(not _cached("football_data_uk/1112/SP1.csv"), reason="results not cached")
def test_reproduces_real_laliga_champion():
    t = reproduce_table(CACHE, "SP1", 2011)
    # Real Madrid won La Liga 2011-12 with a record 100 points.
    assert t["champion"] == "Real Madrid"
    assert t["champion_points"] == 100
    assert t["teams"] == 20


@pytest.mark.skipif(not _cached("football_data_uk/1011/E0.csv"), reason="results not cached")
def test_reproduces_real_epl_champion():
    t = reproduce_table(CACHE, "E0", 2010)
    # Manchester United won the 2010-11 Premier League.
    assert t["champion"] == "Man United"
    assert t["teams"] == 20
    assert t["matches"] == 380
