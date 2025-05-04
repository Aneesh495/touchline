"""Batch season simulation serving with bounded resources and caching.

The serving path for simulations runs a batch of scenarios (each a set of team
strengths and a rules configuration) through the Monte Carlo simulator, caching
results by a scenario key so a repeated scenario is not recomputed. Resources are
bounded: a maximum number of draws per request and a maximum number of scenarios
per batch, rejected rather than silently capped.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from touchline.serving.cache import LRUCache
from touchline.simulate.monte_carlo import SeasonSimulator, SimulationResult
from touchline.simulate.rules import LeagueRules


class SimBoundsExceeded(ValueError):
    pass


@dataclass(frozen=True)
class SimScenario:
    key: str  # stable identity for caching
    teams: tuple[str, ...]
    expected_goals: dict[tuple[str, str], tuple[float, float]]  # (lam, mu) per fixture
    n_sims: int


@dataclass(frozen=True)
class BatchSimBounds:
    max_sims: int = 200000
    max_scenarios: int = 32


class BatchSimulationService:
    def __init__(self, bounds: BatchSimBounds | None = None, cache_capacity: int = 64):
        self.bounds = bounds or BatchSimBounds()
        self.cache: LRUCache = LRUCache(cache_capacity)

    def run(self, scenario: SimScenario, seed: int = 0) -> SimulationResult:
        if scenario.n_sims > self.bounds.max_sims:
            raise SimBoundsExceeded(
                f"{scenario.n_sims} draws exceeds max {self.bounds.max_sims}"
            )
        cached = self.cache.get(scenario.key)
        if cached is not None:
            return cached
        teams = list(scenario.teams)
        remaining = list(scenario.expected_goals.keys())

        def sampler(h, a, rng):
            lam, mu = scenario.expected_goals[(h, a)]
            return int(rng.poisson(lam)), int(rng.poisson(mu))

        result = SeasonSimulator(teams, LeagueRules(), [], remaining).simulate(
            sampler, n_sims=scenario.n_sims, seed=seed
        )
        self.cache.put(scenario.key, result)
        return result

    def run_batch(self, scenarios: list[SimScenario], seed: int = 0) -> list[SimulationResult]:
        if len(scenarios) > self.bounds.max_scenarios:
            raise SimBoundsExceeded(
                f"{len(scenarios)} scenarios exceeds max {self.bounds.max_scenarios}"
            )
        return [self.run(s, seed=seed + i) for i, s in enumerate(scenarios)]

    @staticmethod
    def scenario_from_strengths(
        key: str, teams: list[str], attack: dict[str, float], home_adv: float, n_sims: int
    ) -> SimScenario:
        """Build a scenario's per-fixture expected goals from attack strengths."""
        eg: dict[tuple[str, str], tuple[float, float]] = {}
        for h in teams:
            for a in teams:
                if h == a:
                    continue
                lam = float(np.exp(0.1 + home_adv + attack[h] - attack[a]))
                mu = float(np.exp(0.1 + attack[a] - attack[h]))
                eg[(h, a)] = (lam, mu)
        return SimScenario(key, tuple(teams), eg, n_sims)
