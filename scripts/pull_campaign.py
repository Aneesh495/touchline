"""Large resumable acquisition across multiple competition-seasons.

Pulls match and event files for a configured set of (competition, season) pairs
until a target event count is reached or the budget is exhausted. Fully resumable:
cached files are not re-fetched and do not consume budget, so re-running continues
from where it stopped. Writes a real coverage report and the running event total.

Usage: python scripts/pull_campaign.py [target_events]
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

# Men's competitions with open event data, in pull priority order.
PLAN: list[tuple[int, int, str, str]] = [
    (11, 90, "LALIGA", "2020-2021"),
    (11, 42, "LALIGA", "2019-2020"),
    (11, 4, "LALIGA", "2018-2019"),
    (11, 1, "LALIGA", "2017-2018"),
    (11, 2, "LALIGA", "2016-2017"),
    (11, 27, "LALIGA", "2015-2016"),
    (11, 26, "LALIGA", "2014-2015"),
    (11, 25, "LALIGA", "2013-2014"),
    (11, 24, "LALIGA", "2012-2013"),
    (11, 23, "LALIGA", "2011-2012"),
    (11, 22, "LALIGA", "2010-2011"),
    (11, 21, "LALIGA", "2009-2010"),
    (11, 41, "LALIGA", "2008-2009"),
    (7, 235, "LIGUE1", "2022-2023"),
    (7, 108, "LIGUE1", "2021-2022"),
    (9, 281, "BUNDESLIGA", "2023-2024"),
]


def main() -> int:
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 500_000
    cache = ContentCache(Path("data/raw/cache"))
    # Generous budget; cached files do not consume it.
    budget = RequestBudget(max_requests=2000, min_interval_s=0.15)
    acq = Acquirer(cache, budget, http_fetcher(30), "StatsBomb open data")

    coverage = CoverageMatrix()
    total_events = 0
    total_shots = 0
    processed = 0

    for cid, sid, code, season in PLAN:
        mref = statsbomb_matches_ref(cid, sid)
        try:
            acq.acquire(mref.key, mref.url)
        except Exception as exc:
            print(f"matches fetch failed {code} {season}: {exc}", flush=True)
            continue
        matches = json.loads(cache.get(mref.key).decode())
        for m in matches:
            if total_events >= target:
                break
            summary = parse_statsbomb_match(m)
            eref = statsbomb_events_ref(int(summary["match_id"]))
            try:
                acq.acquire(eref.key, eref.url)
            except Exception as exc:
                print(f"stopped: {exc}", flush=True)
                _report(coverage, total_events, total_shots, processed, budget)
                return 0
            try:
                evs, shots = parse_statsbomb_events(
                    cache.get(eref.key).decode(), home_team_id=summary["home_team_id"]
                )
            except Exception:
                continue
            has_tracking = any(e.raw.get("freeze_frame") for e in evs)
            coverage.add_match(code, season, summary["match_id"],
                               has_events=True, has_tracking=has_tracking)
            total_events += len(evs)
            total_shots += len(shots)
            processed += 1
            if processed % 25 == 0:
                print(f"  {processed} matches, {total_events} events "
                      f"(budget {budget.used})", flush=True)
        if total_events >= target:
            break

    _report(coverage, total_events, total_shots, processed, budget)
    return 0


def _report(coverage, total_events, total_shots, processed, budget) -> None:
    rep = coverage.report()
    print("\n=== coverage ===", flush=True)
    for row in rep:
        print(f"  {row}", flush=True)
    print(f"matches={processed} events={total_events} shots={total_shots} "
          f"budget_used={budget.used}", flush=True)
    Path("data").mkdir(exist_ok=True)
    Path("data/coverage_report.json").write_text(json.dumps(rep, indent=2))
    Path("data/campaign_totals.json").write_text(
        json.dumps({"matches": processed, "events": total_events, "shots": total_shots}, indent=2)
    )


if __name__ == "__main__":
    raise SystemExit(main())
