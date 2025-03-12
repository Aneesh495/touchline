"""Real-data pipeline test. Skips cleanly when no cached StatsBomb data exists.

This exercises the parsers and feature pipeline on genuine acquired data when it is
present (after an ingest), and is skipped in the offline CI run. It never downloads.
"""

from pathlib import Path

import pytest

CACHE = Path("data/raw/cache")
MATCHES_KEY = "statsbomb/matches/11/90.json"


def _have_cached_data() -> bool:
    index = CACHE / "index.json"
    if not index.exists():
        return False
    import json

    idx = json.loads(index.read_text())
    return MATCHES_KEY in idx


@pytest.mark.skipif(not _have_cached_data(), reason="no cached StatsBomb data")
def test_pipeline_builds_real_coverage_and_shots():
    from touchline.pipeline.statsbomb_pipeline import build_from_cache

    res = build_from_cache(CACHE, 11, 90, "LALIGA", "2020-2021", max_matches=5)
    # Real matches produce a non-trivial number of shots and events.
    assert res.n_shots > 50
    assert res.features.shape[1] == 7
    # Coverage reflects real event depth.
    report = res.coverage.report()
    assert report[0]["event_matches"] >= 1
    # Labels are binary goal indicators.
    assert set(res.labels.tolist()) <= {0.0, 1.0}


@pytest.mark.skipif(not _have_cached_data(), reason="no cached StatsBomb data")
def test_real_shots_have_plausible_goal_rate():
    from touchline.pipeline.statsbomb_pipeline import build_from_cache

    res = build_from_cache(CACHE, 11, 90, "LALIGA", "2020-2021", max_matches=5)
    goal_rate = float(res.labels.mean())
    # Real football shot conversion sits broadly in the 8-16% range.
    assert 0.05 < goal_rate < 0.25
