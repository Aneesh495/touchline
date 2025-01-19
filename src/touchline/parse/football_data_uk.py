"""Parser for football-data.co.uk historical CSV result files.

These files carry one row per match with full-time and half-time goals, the
result, and, where available, match statistics: shots (HS/AS), shots on target
(HST/AST), corners (HC/AC), fouls (HF/AF), yellow and red cards (HY/AY, HR/AR).
The column meanings are documented at football-data.co.uk/notes.txt and encoded
here. Only the sporting columns are read; betting-odds columns are ignored.

The division code (``Div``) is mapped to a Touchline-stable competition code so
E0 becomes EPL, SP1 becomes LALIGA, and so on. Rows that lack goals are skipped
and counted as malformed rather than silently coerced to 0-0.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime

# football-data division code -> Touchline competition code.
DIV_TO_COMPETITION = {
    "E0": "EPL",
    "SP1": "LALIGA",
    "D1": "BUNDESLIGA",
    "I1": "SERIEA",
    "F1": "LIGUE1",
}


@dataclass(frozen=True)
class FootballDataMatch:
    """A match-level record from football-data.co.uk in canonical-ready form."""

    competition_code: str
    season: str
    match_date: date | None
    home_team: str
    away_team: str
    fthg: int  # full-time home goals
    ftag: int
    hthg: int | None  # half-time home goals
    htag: int | None
    result: str  # H / D / A
    home_shots: int | None
    away_shots: int | None
    home_shots_on_target: int | None
    away_shots_on_target: int | None
    home_corners: int | None
    away_corners: int | None
    home_fouls: int | None
    away_fouls: int | None
    home_yellows: int | None
    away_yellows: int | None
    home_reds: int | None
    away_reds: int | None
    referee: str | None

    def unique_key(self) -> str:
        """A stable identity for de-duplication across feeds and revisions."""
        d = self.match_date.isoformat() if self.match_date else "?"
        return f"{self.competition_code}|{self.season}|{d}|{self.home_team}|{self.away_team}"


def _int(row: dict, key: str) -> int | None:
    v = row.get(key, "").strip()
    if v == "":
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def _parse_date(raw: str) -> date | None:
    raw = raw.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _season_from_date(d: date | None) -> str:
    if d is None:
        return "unknown"
    # European seasons span Aug-May; July onward belongs to the season starting
    # that calendar year.
    if d.month >= 7:
        return f"{d.year}-{d.year + 1}"
    return f"{d.year - 1}-{d.year}"


def parse_football_data_uk_csv(
    data: bytes | str, season_hint: str | None = None
) -> tuple[list[FootballDataMatch], int]:
    """Parse a CSV file. Returns (matches, malformed_count).

    ``season_hint`` overrides the date-derived season for files that cover a known
    single season. Malformed rows (missing goals, unknown division) are counted,
    not fabricated.
    """
    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
    reader = csv.DictReader(io.StringIO(text))
    out: list[FootballDataMatch] = []
    malformed = 0
    for row in reader:
        div = (row.get("Div") or "").strip()
        comp = DIV_TO_COMPETITION.get(div)
        fthg = _int(row, "FTHG")
        ftag = _int(row, "FTAG")
        if comp is None or fthg is None or ftag is None:
            malformed += 1
            continue
        d = _parse_date(row.get("Date", ""))
        result = (row.get("FTR") or row.get("Res") or "").strip().upper()
        if result not in ("H", "D", "A"):
            result = "H" if fthg > ftag else "A" if ftag > fthg else "D"
        out.append(
            FootballDataMatch(
                competition_code=comp,
                season=season_hint or _season_from_date(d),
                match_date=d,
                home_team=(row.get("HomeTeam") or "").strip(),
                away_team=(row.get("AwayTeam") or "").strip(),
                fthg=fthg,
                ftag=ftag,
                hthg=_int(row, "HTHG"),
                htag=_int(row, "HTAG"),
                result=result,
                home_shots=_int(row, "HS"),
                away_shots=_int(row, "AS"),
                home_shots_on_target=_int(row, "HST"),
                away_shots_on_target=_int(row, "AST"),
                home_corners=_int(row, "HC"),
                away_corners=_int(row, "AC"),
                home_fouls=_int(row, "HF"),
                away_fouls=_int(row, "AF"),
                home_yellows=_int(row, "HY"),
                away_yellows=_int(row, "AY"),
                home_reds=_int(row, "HR"),
                away_reds=_int(row, "AR"),
                referee=(row.get("Referee") or "").strip() or None,
            )
        )
    return out, malformed
