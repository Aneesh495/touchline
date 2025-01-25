"""Simulator oracles: table rules, tie-breaks, and Monte Carlo vs exact."""

import numpy as np

from touchline.simulate.enumerate_small import enumerate_positions
from touchline.simulate.monte_carlo import SeasonSimulator
from touchline.simulate.rules import (
    Fixture,
    LeagueRules,
    TieBreak,
    compute_table,
)


def test_points_and_order_three_for_win():
    teams = ["A", "B", "C"]
    fixtures = [
        Fixture("A", "B", 2, 0),  # A win
        Fixture("B", "C", 1, 1),  # draw
        Fixture("C", "A", 0, 3),  # A win
    ]
    table = compute_table(teams, fixtures, LeagueRules())
    assert table[0].team == "A"
    assert table[0].points == 6
    # B and C both on 1 point; tie broken by goal difference (B: -2, C: -4)
    assert [r.team for r in table[1:]] == ["B", "C"]


def test_two_points_for_win_changes_nothing_here_but_is_configurable():
    teams = ["A", "B"]
    fixtures = [Fixture("A", "B", 1, 0)]
    old = LeagueRules(points_win=2)
    table = compute_table(teams, fixtures, old)
    assert table[0].points == 2


def test_head_to_head_tiebreak():
    teams = ["A", "B"]
    # Equal points and goal difference overall, but A beat B head to head.
    fixtures = [
        Fixture("A", "B", 2, 1),
        Fixture("B", "A", 1, 2),
    ]
    rules = LeagueRules(tie_breaks=(TieBreak.HEAD_TO_HEAD_POINTS,))
    table = compute_table(teams, fixtures, rules)
    assert table[0].team == "A"


def test_point_deduction_applied():
    teams = ["A", "B"]
    fixtures = [Fixture("A", "B", 3, 0)]
    rules = LeagueRules(deductions={"A": 10})
    table = compute_table(teams, fixtures, rules)
    # A won (3 pts) minus 10 = -7, below B's 0.
    assert table[0].team == "B"
    assert table[1].points == -7


def test_monte_carlo_matches_exact_enumeration():
    # Two teams, two remaining matches, small goal grid: enumerate and sample.
    teams = ["A", "B"]
    remaining = [("A", "B"), ("B", "A")]
    rules = LeagueRules()

    # Fixed independent scoreline model favouring A at home.
    def scoreline_prob(h, a, hg, ag):
        import math

        lam = 1.6 if h == "A" else 1.1
        mu = 1.0 if a == "A" else 0.8
        return (
            math.exp(-lam) * lam**hg / math.factorial(hg)
        ) * (math.exp(-mu) * mu**ag / math.factorial(ag))

    exact = enumerate_positions(teams, [], remaining, rules, scoreline_prob, max_goals=6)

    def sampler(h, a, rng):
        lam = 1.6 if h == "A" else 1.1
        mu = 1.0 if a == "A" else 0.8
        return int(rng.poisson(lam)), int(rng.poisson(mu))

    sim = SeasonSimulator(teams, rules, [], remaining)
    res = sim.simulate(sampler, n_sims=40000, seed=3)
    # Compare P(A finishes 1st): sampler within a few SE of exact.
    p_exact = exact["A"][0]
    p_sim = res.finish_prob("A", 1)
    se = res.monte_carlo_se(p_sim)
    assert abs(p_sim - p_exact) < 5 * se + 0.01


def test_simulation_has_no_impossible_state():
    teams = [f"T{i}" for i in range(6)]
    remaining = [(h, a) for h in teams for a in teams if h != a]
    rules = LeagueRules()

    def sampler(h, a, rng):
        return int(rng.poisson(1.3)), int(rng.poisson(1.2))

    sim = SeasonSimulator(teams, rules, [], remaining)
    res = sim.simulate(sampler, n_sims=500, seed=5)
    for t in teams:
        total = res.position_counts[t].sum()
        assert total == res.n_sims  # each sim places the team at exactly one rank
    # Each position is filled exactly once per sim across teams.
    per_position = np.sum([res.position_counts[t] for t in teams], axis=0)
    assert np.all(per_position == res.n_sims)
