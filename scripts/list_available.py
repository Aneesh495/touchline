"""List cached event files and available StatsBomb competitions by match volume."""

import json
from collections import Counter
from pathlib import Path

from touchline.ingest.cache import ContentCache
from touchline.parse.statsbomb import parse_statsbomb_competitions


def main() -> None:
    cache = ContentCache(Path("data/raw/cache"))
    idx_path = Path("data/raw/cache/index.json")
    idx = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    event_keys = [k for k in idx if k.startswith("statsbomb/events/")]
    print("cached event files:", len(event_keys))

    comp_key = "statsbomb/competitions.json"
    if comp_key in idx:
        comps = parse_statsbomb_competitions(cache.get(comp_key))
        by_comp: Counter = Counter()
        names: dict = {}
        for c in comps:
            by_comp[c.competition_id] += 1
            names[c.competition_id] = c.competition_name
        print("competitions with season counts (top 20):")
        for cid, n in sorted(by_comp.items(), key=lambda kv: -kv[1])[:20]:
            print(f"  id={cid:5d} seasons={n:2d}  {names[cid]}")
        # also list all (comp, season) pairs for men's domestic leagues + UCL
        print("\nall (comp_id, season_id, name, season) pairs:")
        for c in comps:
            print(f"  {c.competition_id:5d} {c.season_id:5d}  {c.competition_name} / {c.season_name} 360={c.has_360}")


if __name__ == "__main__":
    main()
