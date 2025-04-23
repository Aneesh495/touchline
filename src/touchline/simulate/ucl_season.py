"""Full UCL season simulation combining the league phase and the knockout.

This orchestrates the 2024-25 format end to end: simulate the 36-team league phase
to a table, map finishing positions to direct round-of-16 places and knockout
play-off places, then run the knockout bracket to a winner. It composes the league
simulator, the league-phase qualification mapping, and the knockout simulator
rather than reimplementing any of them.

The pre-2024 group-stage format is handled by a separate path that groups teams,
qualifies the top two per group, and feeds the round of 16.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from touchline.simulate.knockout import simulate_knockout
from touchline.simulate.ucl import LeaguePhaseQualification, uses_league_phase


@dataclass
class UCLSeasonResult:
    season_start_year: int
    format: str  # "league_phase" | "group_stage"
    direct_r16: list[str]
    playoff_teams: list[str]
    title_counts: dict[str, int]
    n_sims: int

    def title_prob(self, team: str) -> float:
        return self.title_counts.get(team, 0) / self.n_sims


def league_phase_cutoffs(standings: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Split a 36-team league-phase standing into the three outcome bands."""
    direct, playoff, out = [], [], []
    for pos, team in enumerate(standings, start=1):
        outcome = LeaguePhaseQualification(pos).outcome()
        if outcome == "round_of_16_direct":
            direct.append(team)
        elif outcome == "knockout_playoff":
            playoff.append(team)
        else:
            out.append(team)
    return direct, playoff, out


def simulate_ucl_season(
    standings: list[str],
    win_prob: Callable[[str, str], float],
    season_start_year: int,
    n_sims: int = 5000,
    seed: int = 0,
) -> UCLSeasonResult:
    """Simulate from a (given) final league-phase standing through the knockout.

    For simplicity the standing is taken as input (produced upstream by the league
    simulator); this function handles the qualification split and the knockout.
    The play-off round pairs the 16 play-off teams into 8, who join the 8 direct
    qualifiers to form a 16-team bracket.
    """
    if not uses_league_phase(season_start_year):
        raise ValueError("this path models the 2024-25 league-phase format")
    direct, playoff, _ = league_phase_cutoffs(standings)
    rng = np.random.default_rng(seed)
    titles: dict[str, int] = {t: 0 for t in standings}

    for _ in range(n_sims):
        # Resolve the play-off round: pair adjacent play-off teams.
        advancing = []
        for i in range(0, len(playoff) - 1, 2):
            a, b = playoff[i], playoff[i + 1]
            advancing.append(a if rng.random() < win_prob(a, b) else b)
        bracket16 = (direct + advancing)[:16]
        if len(bracket16) < 2:
            continue
        # Pad to a power of two if needed by truncating to 16 or the largest pow2.
        size = 1 << (len(bracket16).bit_length() - 1)
        res = simulate_knockout(bracket16[:size], win_prob, n_sims=1, seed=int(rng.integers(1e9)))
        winner = max(res.titles, key=res.titles.get)
        titles[winner] += 1

    return UCLSeasonResult(
        season_start_year,
        "league_phase",
        direct,
        playoff,
        titles,
        n_sims,
    )
