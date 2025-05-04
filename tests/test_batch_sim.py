"""Batch simulation serving oracles."""

import pytest

from touchline.serving.batch_sim import (
    BatchSimBounds,
    BatchSimulationService,
    SimBoundsExceeded,
)


def _scenario(key, n_sims=500):
    teams = ["A", "B", "C", "D"]
    attack = {"A": 0.5, "B": 0.0, "C": -0.2, "D": -0.4}
    return BatchSimulationService.scenario_from_strengths(key, teams, attack, 0.3, n_sims)


def test_batch_sim_runs_and_caches():
    svc = BatchSimulationService()
    s = _scenario("sc1")
    r1 = svc.run(s, seed=1)
    misses_before = svc.cache.misses
    r2 = svc.run(s, seed=1)  # same key -> cache hit, same object
    assert r1 is r2
    assert svc.cache.misses == misses_before  # no new miss


def test_batch_sim_rejects_too_many_draws():
    svc = BatchSimulationService(bounds=BatchSimBounds(max_sims=100))
    with pytest.raises(SimBoundsExceeded):
        svc.run(_scenario("big", n_sims=101))


def test_batch_sim_rejects_too_many_scenarios():
    svc = BatchSimulationService(bounds=BatchSimBounds(max_scenarios=2))
    with pytest.raises(SimBoundsExceeded):
        svc.run_batch([_scenario(f"s{i}") for i in range(3)])


def test_strongest_team_leads_title_odds():
    svc = BatchSimulationService()
    res = svc.run(_scenario("sc", n_sims=3000), seed=2)
    probs = {t: res.top_n_prob(t, 1) for t in ["A", "B", "C", "D"]}
    assert max(probs, key=probs.get) == "A"
