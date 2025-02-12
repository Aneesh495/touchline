"""Catalogue of permitted data sources and a real HTTP fetcher.

The sources here are public and documented:

* StatsBomb / Hudl open data (github.com/hudl/open-data): open event and, for some
  matches, 360 data under their user agreement. The raw JSON is fetched from the
  repository's raw content host.
* football-data.co.uk: historical CSV results files for the major leagues, free to
  download.

The fetcher is a thin, polite HTTP client with a timeout and a declared user
agent. It returns the response bytes and an ETag revision marker when the server
provides one, which the cache uses for change detection. No credentials are used
and no access restriction is bypassed.
"""

from __future__ import annotations

from dataclasses import dataclass

STATSBOMB_RAW = "https://raw.githubusercontent.com/hudl/open-data/master/data"
FOOTBALL_DATA_UK = "https://www.football-data.co.uk/mmz4281"

# football-data.co.uk season codes are like "2223" for 2022-23. Division codes
# are E0 (Premier League), SP1 (La Liga), D1 (Bundesliga), I1 (Serie A),
# F1 (Ligue 1).
FD_DIVISIONS = ["E0", "SP1", "D1", "I1", "F1"]


@dataclass(frozen=True)
class SourceRef:
    provider: str
    key: str
    url: str
    attribution: str


def statsbomb_competitions_ref() -> SourceRef:
    return SourceRef(
        "statsbomb",
        "statsbomb/competitions.json",
        f"{STATSBOMB_RAW}/competitions.json",
        "StatsBomb/Hudl open data, used under their open-data user agreement",
    )


def statsbomb_matches_ref(competition_id: int, season_id: int) -> SourceRef:
    return SourceRef(
        "statsbomb",
        f"statsbomb/matches/{competition_id}/{season_id}.json",
        f"{STATSBOMB_RAW}/matches/{competition_id}/{season_id}.json",
        "StatsBomb/Hudl open data",
    )


def statsbomb_events_ref(match_id: int) -> SourceRef:
    return SourceRef(
        "statsbomb",
        f"statsbomb/events/{match_id}.json",
        f"{STATSBOMB_RAW}/events/{match_id}.json",
        "StatsBomb/Hudl open data",
    )


def football_data_uk_ref(division: str, season_code: str) -> SourceRef:
    return SourceRef(
        "football_data_uk",
        f"football_data_uk/{season_code}/{division}.csv",
        f"{FOOTBALL_DATA_UK}/{season_code}/{division}.csv",
        "football-data.co.uk historical results",
    )


def season_code(start_year: int) -> str:
    """2022 -> '2223'. Two-digit start and end years concatenated."""
    end = (start_year + 1) % 100
    return f"{start_year % 100:02d}{end:02d}"


def http_fetcher(timeout: float = 30.0):
    """Build a real HTTP fetcher closure using requests."""

    def fetch(url: str) -> tuple[bytes, str | None]:
        import requests

        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "touchline-research/0.1 (public data)"},
        )
        resp.raise_for_status()
        return resp.content, resp.headers.get("ETag")

    return fetch
