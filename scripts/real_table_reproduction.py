"""Reproduce real completed league tables from football-data.co.uk results.

For each (league, season) with full results cached, build the final table with the
rules engine and record the champion and the full standing. This reproduces actual
completed tables from official results, which is gate G09's requirement. It also
runs a rolling-origin Elo result forecast per league to report out-of-time proper
scores on real matches.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from touchline.features.team_strength import MatchRow
from touchline.ingest.cache import ContentCache
from touchline.ingest.sources import FD_DIVISIONS, football_data_uk_ref, season_code
from touchline.parse.football_data_uk import DIV_TO_COMPETITION, parse_football_data_uk_csv

CACHE = Path("data/raw/cache")


def _load_season(div: str, year: int):
    sc = season_code(year)
    ref = football_data_uk_ref(div, sc)
    cache = ContentCache(CACHE)
    data = cache.get(ref.key)
    if data is None:
        return []
    matches, _ = parse_football_data_uk_csv(data)
    return matches


def reproduce_tables(years):
    """Reproduce final tables for every cached (league, season)."""
    from touchline.analysis.tables import reproduce_all

    return reproduce_all(CACHE, years)


def rolling_forecast(div: str, years):
    """Rolling-origin Elo result forecast across seasons of one league."""
    all_matches = []
    for year in years:
        for m in _load_season(div, year):
            d = m.match_date or date(year, 8, 1)
            all_matches.append(
                MatchRow(m.home_team, m.away_team, m.fthg, m.ftag, d,
                         DIV_TO_COMPETITION[div], f"{year}-{year + 1}")
            )
    all_matches.sort(key=lambda r: r.when)
    if len(all_matches) < 500:
        return None
    # train on the first 70%, test on the last 30% (strictly later)
    cut = int(0.7 * len(all_matches))
    elo = _elo(all_matches[:cut])
    base = _base_rates([m.result for m in all_matches[:cut]])
    test = all_matches[cut:]
    ll = _ll(elo, test)
    bll = _ll_const(base, test)
    return {"competition": DIV_TO_COMPETITION[div], "train": cut, "test": len(test),
            "elo_log_loss": ll, "base_log_loss": bll}


def _elo(train):
    from touchline.models.elo import EloModel

    e = EloModel()
    for m in sorted(train, key=lambda r: r.when):
        e.update(m.home, m.away, m.home_goals, m.away_goals)
    return e


def _base_rates(results):
    n = len(results) or 1
    return (results.count("H") / n, results.count("D") / n, results.count("A") / n)


def _ll(elo, test):
    import numpy as np

    tot = 0.0
    for m in test:
        ph, pd, pa = elo.predict_result_probs(m.home, m.away)
        tot += -np.log(max({"H": ph, "D": pd, "A": pa}[m.result], 1e-12))
    return tot / max(len(test), 1)


def _ll_const(base, test):
    import numpy as np

    ph, pd, pa = base
    probs = {"H": ph, "D": pd, "A": pa}
    tot = sum(-np.log(max(probs[m.result], 1e-12)) for m in test)
    return tot / max(len(test), 1)


def main() -> int:
    years = list(range(2010, 2024))
    tables = reproduce_tables(years)
    forecasts = [f for div in FD_DIVISIONS if (f := rolling_forecast(div, years))]

    print(f"reproduced {len(tables)} real league tables", flush=True)
    for t in tables[:12]:
        print(f"  {t['competition']} {t['season']}: champion {t['champion']} "
              f"({t['champion_points']} pts), {t['teams']} teams, {t['matches']} matches",
              flush=True)
    print("\nrolling Elo forecast (real matches):", flush=True)
    for f in forecasts:
        verdict = "beats base" if f["elo_log_loss"] < f["base_log_loss"] else "below base"
        print(f"  {f['competition']}: Elo {f['elo_log_loss']:.4f} vs base "
              f"{f['base_log_loss']:.4f} ({verdict})", flush=True)

    out = {"tables_reproduced": len(tables), "tables": tables, "forecasts": forecasts}
    Path("docs/research/real_tables.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote docs/research/real_tables.json ({len(tables)} tables)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
