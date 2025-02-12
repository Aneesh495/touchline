"""UEFA Champions League rules across eras.

The competition's structure changed, so a single hardcoded format would be wrong
for most seasons. This module models the pieces explicitly and selects them by
season:

* Group stage (through 2023-24): eight groups of four, top two advance, round of
  16 onward as two-legged knockouts.
* League phase (from 2024-25): a single 36-team table, each club plays eight
  different opponents, top eight advance directly to the round of 16 and ninth
  through twenty-fourth contest a knockout play-off.

Two-legged ties are decided on aggregate. The away-goals rule applied through
2020-21 and was abolished from 2021-22; this module applies it only in the seasons
where it was in force, and never after. A tie still level after the second leg
goes to extra time and, if needed, a penalty shootout.
"""

from __future__ import annotations

from dataclasses import dataclass


def away_goals_in_force(season_start_year: int) -> bool:
    """Away goals applied up to and including 2020-21; abolished from 2021-22."""
    return season_start_year <= 2020


def uses_league_phase(season_start_year: int) -> bool:
    """The 36-team league phase began in 2024-25."""
    return season_start_year >= 2024


@dataclass(frozen=True)
class LegResult:
    home: str
    away: str
    home_goals: int
    away_goals: int


@dataclass(frozen=True)
class TieOutcome:
    winner: str
    reason: str  # "aggregate" | "away_goals" | "extra_time" | "penalties"
    aggregate_home: int
    aggregate_away: int


def decide_two_legged_tie(
    team_a: str,
    team_b: str,
    leg1: LegResult,
    leg2: LegResult,
    season_start_year: int,
    extra_time_goals: tuple[int, int] = (0, 0),
    shootout: tuple[int, int] | None = None,
) -> TieOutcome:
    """Decide a two-legged tie under the rules of the given season.

    ``leg1`` is hosted by team_a, ``leg2`` by team_b. Aggregate is summed across
    both legs. If away goals are in force and the aggregate is level, the team with
    more away goals advances. Otherwise a level tie goes to extra time in the
    second leg (``extra_time_goals`` added to team_b-home leg) and then penalties.
    """
    # Aggregate from team_a's perspective.
    a_goals = leg1.home_goals + leg2.away_goals
    b_goals = leg1.away_goals + leg2.home_goals
    if a_goals > b_goals:
        return TieOutcome(team_a, "aggregate", a_goals, b_goals)
    if b_goals > a_goals:
        return TieOutcome(team_b, "aggregate", a_goals, b_goals)

    # Level on aggregate.
    if away_goals_in_force(season_start_year):
        a_away = leg2.away_goals  # team_a scored these away in leg 2
        b_away = leg1.away_goals  # team_b scored these away in leg 1
        if a_away > b_away:
            return TieOutcome(team_a, "away_goals", a_goals, b_goals)
        if b_away > a_away:
            return TieOutcome(team_b, "away_goals", a_goals, b_goals)

    # Extra time in the second leg.
    et_a, et_b = extra_time_goals
    a_goals += et_a
    b_goals += et_b
    if a_goals > b_goals:
        return TieOutcome(team_a, "extra_time", a_goals, b_goals)
    if b_goals > a_goals:
        return TieOutcome(team_b, "extra_time", a_goals, b_goals)
    # Note: after 2021-22 extra-time away goals never counted; we do not apply
    # away-goals in extra time in any season per the final 2019 clarification.

    # Penalties.
    if shootout is None:
        raise ValueError("tie level after extra time requires a shootout result")
    sa, sb = shootout
    winner = team_a if sa > sb else team_b
    return TieOutcome(winner, "penalties", a_goals, b_goals)


@dataclass(frozen=True)
class LeaguePhaseQualification:
    """How a club's league-phase finishing position maps to the next round."""

    position: int

    def outcome(self) -> str:
        if self.position <= 8:
            return "round_of_16_direct"
        if self.position <= 24:
            return "knockout_playoff"
        return "eliminated"


def group_stage_qualifies(position_in_group: int) -> bool:
    """Top two of a four-team group advance in the pre-2024 format."""
    return position_in_group <= 2
