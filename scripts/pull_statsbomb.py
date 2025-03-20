"""Acquire a competition's matches and events from StatsBomb open data.

Resumable and budgeted. Writes nothing to git (data lives under data/raw). Prints a
coverage summary with real unique counts. Usage:

    python scripts/pull_statsbomb.py <competition_id> <season_id> <code> <season> [max_matches]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from touchline.coverage.matrix import CoverageMatrix
from touchline.ingest.acquire import Acquirer
from touchline.ingest.budget import RequestBudget
from touchline.ingest.cache import ContentCache
from touchline.ingest.sources import (
    http_fetcher,
    statsbomb_events_ref,
    statsbomb_matches_ref,
)
from touchline.parse.statsbomb import parse_statsbomb_events, parse_statsbomb_match


def main() -> int:
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    sid = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    code = sys.argv[3] if len(sys.argv) > 3 else "LALIGA"
    season = sys.argv[4] if len(sys.argv) > 4 else "2020-2021"
    max_matches = int(sys.argv[5]) if len(sys.argv) > 5 else 30

    cache = ContentCache(Path("data/raw/cache"))
    budget = RequestBudget(max_requests=max_matches + 5, min_interval_s=0.25)
    acq = Acquirer(cache, budget, http_fetcher(30), "StatsBomb open data")

    mref = statsbomb_matches_ref(cid, sid)
    acq.acquire(mref.key, mref.url)
    matches = json.loads(cache.get(mref.key).decode())[:max_matches]

    coverage = CoverageMatrix()
    total_events = 0
    total_shots = 0
    for m in matches:
        summary = parse_statsbomb_match(m)
        eref = statsbomb_events_ref(int(summary["match_id"]))
        try:
            acq.acquire(eref.key, eref.url)
        except Exception as exc:  # budget or network
            print(f"stopped at {summary['match_id']}: {exc}")
            break
        evs, shots = parse_statsbomb_events(
            cache.get(eref.key).decode(), home_team_id=summary["home_team_id"]
        )
        total_events += len(evs)
        total_shots += len(shots)
        has_tracking = any(e.raw.get("freeze_frame") for e in evs)
        coverage.add_match(code, season, summary["match_id"], has_events=True, has_tracking=has_tracking)

    print("coverage", coverage.report())
    print("total_events", total_events)
    print("total_shots", total_shots)
    print("budget_used", budget.used)
    # persist a coverage report artifact under data (ignored by git)
    out = Path("data/coverage_report.json")
    out.write_text(json.dumps(coverage.report(), indent=2))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
