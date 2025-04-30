"""Parser for the openfootball plain-text match format.

openfootball publishes results as human-readable text files, one competition-season
per file, with lines like:

    [Fri Aug/12]
    Crystal Palace  0-2  Arsenal
    Fulham          2-2  Liverpool

Round headers and dates appear on their own lines. This parser reads the match
lines into canonical-ready records, preserving the raw line for audit. It is
tolerant of spacing and skips non-match lines rather than failing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A match line: team, score like "2-1", team. Teams may contain spaces and dots.
_MATCH_RE = re.compile(
    r"^\s*(?P<home>.+?)\s+(?P<hg>\d+)\s*[-:]\s*(?P<ag>\d+)\s+(?P<away>.+?)\s*$"
)
_DATE_RE = re.compile(r"^\s*\[(?P<date>[^\]]+)\]\s*$")
_ROUND_RE = re.compile(r"^\s*(Matchday|Round|Week)\b", re.IGNORECASE)


@dataclass(frozen=True)
class OpenFootballMatch:
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    date_text: str | None
    raw: str

    @property
    def result(self) -> str:
        if self.home_goals > self.away_goals:
            return "H"
        if self.home_goals < self.away_goals:
            return "A"
        return "D"


def parse_openfootball(text: str) -> tuple[list[OpenFootballMatch], int]:
    """Parse an openfootball results file. Returns (matches, skipped_lines)."""
    matches: list[OpenFootballMatch] = []
    skipped = 0
    current_date: str | None = None
    for line in text.splitlines():
        if not line.strip():
            continue
        dm = _DATE_RE.match(line)
        if dm:
            current_date = dm.group("date")
            continue
        if _ROUND_RE.match(line):
            continue
        m = _MATCH_RE.match(line)
        if not m:
            skipped += 1
            continue
        home = m.group("home").strip()
        away = m.group("away").strip()
        # Guard against false positives: a team name of only digits is not a team.
        if home.isdigit() or away.isdigit():
            skipped += 1
            continue
        matches.append(
            OpenFootballMatch(
                home_team=home,
                away_team=away,
                home_goals=int(m.group("hg")),
                away_goals=int(m.group("ag")),
                date_text=current_date,
                raw=line,
            )
        )
    return matches, skipped
