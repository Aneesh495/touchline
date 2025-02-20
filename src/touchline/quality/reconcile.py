"""Reconciliation checks that report discrepancies instead of hiding them.

Known, acceptable reasons for a mismatch (own goals credited to the other side,
provider assist policy, extra-time goals, shootout kicks) are enumerated so a
genuine problem is distinguished from an expected accounting difference. A report
lists each discrepancy with the numbers involved, leaving the decision to a human.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiscrepancyReport:
    match_id: str
    discrepancies: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not self.discrepancies

    def add(self, message: str) -> None:
        self.discrepancies.append(message)


def reconcile_score(
    match_id: str,
    goal_events_home: int,
    goal_events_away: int,
    recorded_home: int,
    recorded_away: int,
    own_goals_for_home: int = 0,
    own_goals_for_away: int = 0,
) -> DiscrepancyReport:
    """Check that goal events plus own goals match the recorded score.

    Own goals are credited to the benefiting team in the recorded score but are
    often recorded as an event by the scoring (wrong-net) player, so they are added
    explicitly. A remaining mismatch is a real discrepancy.
    """
    report = DiscrepancyReport(match_id)
    implied_home = goal_events_home + own_goals_for_home
    implied_away = goal_events_away + own_goals_for_away
    if implied_home != recorded_home:
        report.add(
            f"home: {implied_home} implied (events {goal_events_home} + "
            f"{own_goals_for_home} OG) != {recorded_home} recorded"
        )
    if implied_away != recorded_away:
        report.add(
            f"away: {implied_away} implied (events {goal_events_away} + "
            f"{own_goals_for_away} OG) != {recorded_away} recorded"
        )
    return report


def check_lineup_completeness(
    match_id: str, home_starters: int, away_starters: int
) -> DiscrepancyReport:
    """A valid starting lineup has exactly eleven players per side."""
    report = DiscrepancyReport(match_id)
    if home_starters != 11:
        report.add(f"home has {home_starters} starters, expected 11")
    if away_starters != 11:
        report.add(f"away has {away_starters} starters, expected 11")
    return report


def check_red_card_manpower(
    match_id: str, red_cards: int, manpower_reductions: int
) -> DiscrepancyReport:
    """Each red card should correspond to a manpower reduction event.

    A red card with no manpower change (or vice versa) signals a missing or
    contradictory event stream that should be investigated.
    """
    report = DiscrepancyReport(match_id)
    if red_cards != manpower_reductions:
        report.add(
            f"{red_cards} red cards but {manpower_reductions} manpower reductions"
        )
    return report
