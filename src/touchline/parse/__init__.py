"""Provider-specific parsers that emit canonical domain objects.

A parser's only job is to read a provider's bytes and produce domain objects while
preserving the original payload in ``raw``. Parsers never model or aggregate; they
canonicalise. Each provider has distinct quirks (coordinate frame, taxonomy,
missingness) which are handled here and nowhere else.
"""

from touchline.parse.football_data_uk import parse_football_data_uk_csv
from touchline.parse.openfootball import parse_openfootball
from touchline.parse.statsbomb import (
    StatsBombCompetition,
    parse_statsbomb_competitions,
    parse_statsbomb_events,
    parse_statsbomb_match,
)

__all__ = [
    "parse_statsbomb_events",
    "parse_statsbomb_match",
    "StatsBombCompetition",
    "parse_statsbomb_competitions",
    "parse_football_data_uk_csv",
    "parse_openfootball",
]
