"""Catalogue of competitions with their distinct identities and era rules.

The expanded scope covers domestic leagues and cups, European competitions, super
cups, and the Club World Cup. These are distinct rule and data entities: the
historical annual Club World Cup, the expanded 2025 format, and the separate FIFA
Intercontinental Cup are not the same competition and are not merged into one
rectangular panel. Each entry records the stable code, the kind, and notes on the
era-specific structure so the coverage report and the rules engine agree on what a
competition is.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CompetitionKind(str, Enum):
    LEAGUE = "league"
    DOMESTIC_CUP = "domestic_cup"
    DOMESTIC_SUPER_CUP = "domestic_super_cup"
    EUROPEAN = "european"
    EUROPEAN_SUPER_CUP = "european_super_cup"
    INTERCONTINENTAL = "intercontinental"


@dataclass(frozen=True)
class CompetitionSpec:
    code: str
    name: str
    kind: CompetitionKind
    country: str  # "" for international
    notes: str = ""


CATALOGUE: dict[str, CompetitionSpec] = {
    # Leagues
    "EPL": CompetitionSpec("EPL", "Premier League", CompetitionKind.LEAGUE, "England"),
    "LALIGA": CompetitionSpec("LALIGA", "La Liga", CompetitionKind.LEAGUE, "Spain"),
    "BUNDESLIGA": CompetitionSpec("BUNDESLIGA", "Bundesliga", CompetitionKind.LEAGUE, "Germany"),
    "SERIEA": CompetitionSpec("SERIEA", "Serie A", CompetitionKind.LEAGUE, "Italy"),
    "LIGUE1": CompetitionSpec("LIGUE1", "Ligue 1", CompetitionKind.LEAGUE, "France"),
    # Domestic cups
    "FACUP": CompetitionSpec("FACUP", "FA Cup", CompetitionKind.DOMESTIC_CUP, "England"),
    "COPADELREY": CompetitionSpec("COPADELREY", "Copa del Rey", CompetitionKind.DOMESTIC_CUP, "Spain"),
    "DFBPOKAL": CompetitionSpec("DFBPOKAL", "DFB-Pokal", CompetitionKind.DOMESTIC_CUP, "Germany"),
    "COPPAITALIA": CompetitionSpec("COPPAITALIA", "Coppa Italia", CompetitionKind.DOMESTIC_CUP, "Italy"),
    "COUPEDEFRANCE": CompetitionSpec("COUPEDEFRANCE", "Coupe de France", CompetitionKind.DOMESTIC_CUP, "France"),
    # Domestic super cups / shields
    "COMMUNITYSHIELD": CompetitionSpec("COMMUNITYSHIELD", "FA Community Shield", CompetitionKind.DOMESTIC_SUPER_CUP, "England"),
    "SUPERCOPA": CompetitionSpec("SUPERCOPA", "Supercopa de Espana", CompetitionKind.DOMESTIC_SUPER_CUP, "Spain"),
    # European
    "UCL": CompetitionSpec("UCL", "UEFA Champions League", CompetitionKind.EUROPEAN, "", "group stage pre-2024; league phase from 2024-25"),
    "UEL": CompetitionSpec("UEL", "UEFA Europa League", CompetitionKind.EUROPEAN, ""),
    "UECL": CompetitionSpec("UECL", "UEFA Conference League", CompetitionKind.EUROPEAN, "", "from its 2021-22 inception"),
    "UEFASUPERCUP": CompetitionSpec("UEFASUPERCUP", "UEFA Super Cup", CompetitionKind.EUROPEAN_SUPER_CUP, ""),
    # Intercontinental (kept distinct)
    "CWC_ANNUAL": CompetitionSpec("CWC_ANNUAL", "FIFA Club World Cup (annual format)", CompetitionKind.INTERCONTINENTAL, "", "historical annual editions"),
    "CWC_2025": CompetitionSpec("CWC_2025", "FIFA Club World Cup (2025 expanded)", CompetitionKind.INTERCONTINENTAL, "", "distinct expanded 32-team format"),
    "FIFA_INTERCONTINENTAL": CompetitionSpec("FIFA_INTERCONTINENTAL", "FIFA Intercontinental Cup", CompetitionKind.INTERCONTINENTAL, "", "separate entity from the Club World Cup"),
}


def competitions_by_kind(kind: CompetitionKind) -> list[CompetitionSpec]:
    return [c for c in CATALOGUE.values() if c.kind is kind]


def is_distinct_club_world_cup_entities() -> bool:
    """The annual, 2025 expanded, and Intercontinental Cup are distinct codes."""
    codes = {"CWC_ANNUAL", "CWC_2025", "FIFA_INTERCONTINENTAL"}
    return codes <= set(CATALOGUE)
