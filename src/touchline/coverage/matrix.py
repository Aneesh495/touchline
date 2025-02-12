"""The coverage matrix data structure and reporting.

A cell records, for one (competition, season), the counts that matter for the
coverage gate: unique matches present, matches with event data, matches with
360/tracking data, missing matches, and matches with revisions newer than first
ingest. Field level is an enum so the UI can colour-code the three depths.

Unique counts are computed from identity sets, never from row counts, so a feed
duplicated across providers does not inflate coverage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FieldLevel(str, Enum):
    NONE = "none"
    RESULTS = "results"  # match-level results only
    EVENTS = "events"  # on-ball event data present
    TRACKING = "tracking"  # 360 / tracking freeze frames present


@dataclass
class CoverageCell:
    competition: str
    season: str
    match_ids: set[str] = field(default_factory=set)
    event_match_ids: set[str] = field(default_factory=set)
    tracking_match_ids: set[str] = field(default_factory=set)
    missing_match_ids: set[str] = field(default_factory=set)
    revised_match_ids: set[str] = field(default_factory=set)

    @property
    def n_matches(self) -> int:
        return len(self.match_ids)

    @property
    def n_event_matches(self) -> int:
        return len(self.event_match_ids)

    @property
    def n_tracking_matches(self) -> int:
        return len(self.tracking_match_ids)

    @property
    def field_level(self) -> FieldLevel:
        if self.tracking_match_ids:
            return FieldLevel.TRACKING
        if self.event_match_ids:
            return FieldLevel.EVENTS
        if self.match_ids:
            return FieldLevel.RESULTS
        return FieldLevel.NONE

    def to_dict(self) -> dict:
        return {
            "competition": self.competition,
            "season": self.season,
            "matches": self.n_matches,
            "event_matches": self.n_event_matches,
            "tracking_matches": self.n_tracking_matches,
            "missing": len(self.missing_match_ids),
            "revised": len(self.revised_match_ids),
            "field_level": self.field_level.value,
        }


@dataclass
class CoverageMatrix:
    cells: dict[tuple[str, str], CoverageCell] = field(default_factory=dict)

    def cell(self, competition: str, season: str) -> CoverageCell:
        key = (competition, season)
        if key not in self.cells:
            self.cells[key] = CoverageCell(competition, season)
        return self.cells[key]

    def add_match(
        self,
        competition: str,
        season: str,
        match_id: str,
        has_events: bool = False,
        has_tracking: bool = False,
    ) -> None:
        c = self.cell(competition, season)
        c.match_ids.add(match_id)
        if has_events:
            c.event_match_ids.add(match_id)
        if has_tracking:
            c.tracking_match_ids.add(match_id)

    def total_matches(self) -> int:
        return sum(c.n_matches for c in self.cells.values())

    def total_event_matches(self) -> int:
        return sum(c.n_event_matches for c in self.cells.values())

    def competitions(self) -> set[str]:
        return {c.competition for c in self.cells.values()}

    def seasons_for(self, competition: str) -> set[str]:
        return {c.season for c in self.cells.values() if c.competition == competition}

    def report(self) -> list[dict]:
        return [self.cells[k].to_dict() for k in sorted(self.cells)]

    def meets_profile(
        self, min_matches: int, min_event_matches: int, required_competitions: set[str]
    ) -> tuple[bool, list[str]]:
        """Check the matrix against a coverage profile; return (ok, reasons)."""
        reasons: list[str] = []
        if self.total_matches() < min_matches:
            reasons.append(
                f"matches {self.total_matches()} < required {min_matches}"
            )
        if self.total_event_matches() < min_event_matches:
            reasons.append(
                f"event matches {self.total_event_matches()} < required {min_event_matches}"
            )
        missing = required_competitions - self.competitions()
        if missing:
            reasons.append(f"missing competitions: {sorted(missing)}")
        return (len(reasons) == 0, reasons)
