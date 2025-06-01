"""Acquire football-data.co.uk result CSVs for the five leagues across seasons.

Match-level breadth for all five leagues, where StatsBomb lacks event data. Budgeted
and resumable. Writes a real match-level coverage report. Usage:

    python scripts/pull_football_data.py [start_year] [end_year]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from touchline.coverage.matrix import CoverageMatrix
from touchline.ingest.acquire import Acquirer
from touchline.ingest.budget import RequestBudget
from touchline.ingest.cache import ContentCache
from touchline.ingest.sources import FD_DIVISIONS, football_data_uk_ref, http_fetcher, season_code
from touchline.parse.football_data_uk import DIV_TO_COMPETITION, parse_football_data_uk_csv


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2014
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 2023
    cache = ContentCache(Path("data/raw/cache"))
    budget = RequestBudget(max_requests=400, min_interval_s=0.2)
    acq = Acquirer(cache, budget, http_fetcher(30), "football-data.co.uk")

    coverage = CoverageMatrix()
    total = 0
    malformed_total = 0
    for year in range(start, end + 1):
        sc = season_code(year)
        for div in FD_DIVISIONS:
            ref = football_data_uk_ref(div, sc)
            try:
                acq.acquire(ref.key, ref.url)
            except Exception as exc:
                print(f"skip {div} {sc}: {exc}", flush=True)
                continue
            data = cache.get(ref.key)
            if data is None:
                continue
            matches, malformed = parse_football_data_uk_csv(data)
            malformed_total += malformed
            code = DIV_TO_COMPETITION.get(div, div)
            for m in matches:
                coverage.add_match(code, m.season, m.unique_key(), has_events=False)
            total += len(matches)
        print(f"  through {year}: {total} match-level records "
              f"(budget {budget.used})", flush=True)

    rep = coverage.report()
    print("\n=== match-level coverage ===", flush=True)
    comps = coverage.competitions()
    print(f"competitions: {sorted(comps)}", flush=True)
    print(f"total unique matches: {coverage.total_matches()} "
          f"(malformed skipped: {malformed_total})", flush=True)
    Path("data").mkdir(exist_ok=True)
    Path("data/match_coverage.json").write_text(json.dumps(rep, indent=2))
    # a compact summary for docs
    summary = {
        "source": "football-data.co.uk",
        "competitions": sorted(comps),
        "total_unique_matches": coverage.total_matches(),
        "seasons": sorted({c["season"] for c in rep}),
    }
    Path("data/match_coverage_summary.json").write_text(json.dumps(summary, indent=2))
    print("wrote data/match_coverage.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
