"""Knockout bracket oracles: sampler vs exact, invariants."""

import pytest

from touchline.simulate.knockout import ExactKnockout, simulate_knockout


def _elo_winprob(ratings):
    def wp(a, b):
        import math

        return 1.0 / (1.0 + math.pow(10.0, -(ratings[a] - ratings[b]) / 400.0))

    return wp


def test_bracket_must_be_power_of_two():
    with pytest.raises(ValueError):
        simulate_knockout(["a", "b", "c"], lambda a, b: 0.5, n_sims=10)


def test_sampler_matches_exact_on_four_team_bracket():
    ratings = {"A": 1800, "B": 1500, "C": 1600, "D": 1400}
    wp = _elo_winprob(ratings)
    bracket = ["A", "B", "C", "D"]
    exact = ExactKnockout(bracket, wp).title_probabilities()
    sim = simulate_knockout(bracket, wp, n_sims=40000, seed=1)
    for t in bracket:
        p_sim = sim.title_prob(t)
        se = sim.monte_carlo_se(p_sim)
        assert abs(p_sim - exact[t]) < 5 * se + 0.01
    # title probabilities sum to one
    assert abs(sum(exact.values()) - 1.0) < 1e-9


def test_strongest_team_most_likely_to_win():
    ratings = {"A": 2000, "B": 1500, "C": 1500, "D": 1500}
    sim = simulate_knockout(["A", "B", "C", "D"], _elo_winprob(ratings), n_sims=20000, seed=2)
    probs = {t: sim.title_prob(t) for t in ratings}
    assert max(probs, key=probs.get) == "A"


def test_reach_counts_are_consistent():
    sim = simulate_knockout(["A", "B", "C", "D"], lambda a, b: 0.5, n_sims=1000, seed=3)
    # every team reaches round 0 in every sim
    for t in ["A", "B", "C", "D"]:
        assert sim.reached[t][0] == 1000
    # exactly one team wins each sim
    assert sum(sim.titles.values()) == 1000
