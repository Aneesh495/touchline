"""Monte Carlo season simulation with correlated strength draws.

A season is simulated by drawing a score for every remaining fixture from a match
model, completing the table, and recording each team's final position. Repeating
this many times gives distributions over title, qualification, and relegation.

Two properties matter for honesty:

* Correlation. Team strength is uncertain. Drawing a single strength sample per
  simulated season (rather than fresh independent per-match probabilities) keeps a
  team's good and bad matches correlated through its sampled strength, so the
  spread of outcomes reflects real strength uncertainty rather than only
  match-to-match noise.
* Monte Carlo error. Every reported probability carries a standard error from the
  number of simulations, so a 0.40 title probability from 1,000 draws is not
  presented as more precise than it is.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from touchline.simulate.rules import Fixture, LeagueRules, compute_table


@dataclass(frozen=True)
class SimulationResult:
    teams: list[str]
    n_sims: int
    # position_counts[team][pos] = number of sims team finished at 1-based pos
    position_counts: dict[str, np.ndarray]

    def finish_prob(self, team: str, position: int) -> float:
        return float(self.position_counts[team][position - 1] / self.n_sims)

    def top_n_prob(self, team: str, n: int) -> float:
        return float(self.position_counts[team][:n].sum() / self.n_sims)

    def monte_carlo_se(self, p: float) -> float:
        """Standard error of a probability estimate from n_sims Bernoulli draws."""
        return math.sqrt(max(p * (1 - p), 0.0) / self.n_sims)

    def expected_position(self, team: str) -> float:
        counts = self.position_counts[team]
        positions = np.arange(1, len(self.teams) + 1)
        return float((positions * counts).sum() / self.n_sims)


ScoreSampler = Callable[[str, str, np.random.Generator], tuple[int, int]]


@dataclass
class SeasonSimulator:
    teams: list[str]
    rules: LeagueRules
    played_fixtures: list[Fixture] = field(default_factory=list)
    remaining: list[tuple[str, str]] = field(default_factory=list)

    def simulate(
        self,
        score_sampler: ScoreSampler,
        n_sims: int = 10000,
        seed: int = 0,
        strength_resampler: Callable[[np.random.Generator], None] | None = None,
    ) -> SimulationResult:
        rng = np.random.default_rng(seed)
        n = len(self.teams)
        counts = {t: np.zeros(n, dtype=np.int64) for t in self.teams}
        for _ in range(n_sims):
            # Draw one correlated strength sample for the whole simulated season.
            if strength_resampler is not None:
                strength_resampler(rng)
            fixtures = list(self.played_fixtures)
            for h, a in self.remaining:
                hg, ag = score_sampler(h, a, rng)
                fixtures.append(Fixture(h, a, hg, ag))
            table = compute_table(self.teams, fixtures, self.rules)
            for pos, row in enumerate(table, start=1):
                counts[row.team][pos - 1] += 1
        return SimulationResult(self.teams, n_sims, counts)
