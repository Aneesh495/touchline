"""Persist cached StatsBomb shots into the Arrow/Parquet store and query via DuckDB.

Builds shot tables from the cached event matches and writes them to the columnar
store partitioned by competition and season, then runs a DuckDB goal-rate-by-distance
query over the whole store to show the persistence path works end to end on real
data.
"""

from __future__ import annotations

import json
from pathlib import Path

from touchline.ingest.cache import ContentCache
from touchline.ingest.sources import statsbomb_events_ref, statsbomb_matches_ref
from touchline.parse.statsbomb import parse_statsbomb_events, parse_statsbomb_match
from touchline.store.arrow_store import ArrowStore, shots_to_table
from touchline.store.duck import DuckQuery

CACHE = Path("data/raw/cache")
STORE = Path("data/arrow")
SEASONS = [
    (11, 90, "LALIGA", "2020-2021"),
    (11, 4, "LALIGA", "2018-2019"),
    (11, 42, "LALIGA", "2019-2020"),
]


def main() -> int:
    cache = ContentCache(CACHE)
    store = ArrowStore(STORE)
    written = 0
    for cid, sid, code, season in SEASONS:
        mref = statsbomb_matches_ref(cid, sid)
        mb = cache.get(mref.key)
        if mb is None:
            continue
        matches = json.loads(mb.decode())
        all_shots = []
        for m in matches:
            summary = parse_statsbomb_match(m)
            eb = cache.get(statsbomb_events_ref(int(summary["match_id"])).key)
            if eb is None:
                continue
            _, shots = parse_statsbomb_events(eb.decode(), home_team_id=summary["home_team_id"])
            all_shots.extend(s for s in shots if s.counts_toward_regulation)
        if all_shots:
            table = shots_to_table(all_shots, f"{code}-{season}")
            store.write(code, season, "shots", table, allow_version=True)
            written += len(all_shots)
            print(f"  wrote {len(all_shots)} shots for {code} {season}", flush=True)

    dq = DuckQuery(STORE)
    print(f"\ntotal shots in store: {dq.total_shots()}", flush=True)
    print("goal rate by 5m distance band (real data):", flush=True)
    for band, rate, n in dq.goal_rate_by_distance_band(band_m=5.0):
        print(f"  {band * 5:>2}-{band * 5 + 5:>2}m: rate={rate:.3f} n={n}", flush=True)
    dq.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
