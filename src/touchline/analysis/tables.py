"""Reproduce completed league tables from cached football-data.co.uk results.

Builds the final table for a (league, season) from real cached results using the
rules engine, so a reproduction can be checked against the official historical
record. Lives in the package (not just a script) so tests can import it.
"""

from __future__ import annotations

from pathlib import Path

from touchline.ingest.cache import ContentCache
from touchline.ingest.sources import FD_DIVISIONS, football_data_uk_ref, season_code
from touchline.parse.football_data_uk import DIV_TO_COMPETITION, parse_football_data_uk_csv
from touchline.simulate.rules import Fixture, LeagueRules, compute_table


def load_season_matches(cache_root: Path, div: str, year: int):
    ref = football_data_uk_ref(div, season_code(year))
    data = ContentCache(cache_root).get(ref.key)
    if data is None:
        return []
    matches, _ = parse_football_data_uk_csv(data)
    return matches


def reproduce_table(cache_root: Path, div: str, year: int) -> dict | None:
    matches = load_season_matches(cache_root, div, year)
    if len(matches) < 100:
        return None
    teams = sorted({m.home_team for m in matches} | {m.away_team for m in matches})
    fixtures = [Fixture(m.home_team, m.away_team, m.fthg, m.ftag) for m in matches]
    table = compute_table(teams, fixtures, LeagueRules())
    return {
        "competition": DIV_TO_COMPETITION[div],
        "season": f"{year}-{year + 1}",
        "teams": len(teams),
        "matches": len(matches),
        "champion": table[0].team,
        "champion_points": table[0].points,
        "runner_up": table[1].team,
        "relegated": [r.team for r in table[-3:]],
    }


def reproduce_all(cache_root: Path, years) -> list[dict]:
    out = []
    for year in years:
        for div in FD_DIVISIONS:
            t = reproduce_table(cache_root, div, year)
            if t is not None:
                out.append(t)
    return out
