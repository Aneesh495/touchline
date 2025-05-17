"""Finishing-persistence (H2) oracles using known-truth synthetic data."""

import numpy as np

from touchline.analysis.finishing import PlayerShots, split_half_persistence


def _make_players(true_skill_sd, n_players=120, shots=160, seed=0):
    """Each player has a latent finishing skill; skill_sd=0 means pure noise."""
    rng = np.random.default_rng(seed)
    players = []
    for i in range(n_players):
        skill = rng.normal(0, true_skill_sd)  # log-odds bump to conversion
        goals = []
        xg = []
        for _ in range(shots):
            base = rng.uniform(0.03, 0.4)
            xg.append(base)
            p = 1 / (1 + np.exp(-(np.log(base / (1 - base)) + skill)))
            goals.append(1 if rng.uniform() < p else 0)
        players.append(PlayerShots(f"p{i}", goals, xg))
    return players


def test_persistence_detected_when_skill_exists():
    players = _make_players(true_skill_sd=0.8, seed=1)
    res = split_half_persistence(players, min_shots_per_half=40)
    # With real latent skill, split halves should correlate positively.
    assert res.correlation > 0.1
    assert res.n_players > 10


def test_no_persistence_when_pure_noise():
    players = _make_players(true_skill_sd=0.0, seed=2)
    res = split_half_persistence(players, min_shots_per_half=40)
    # With no latent skill, the CI should include zero (not persistent).
    assert not res.persistent


def test_threshold_disclosed():
    players = _make_players(true_skill_sd=0.5, seed=3)
    res = split_half_persistence(players, min_shots_per_half=50)
    assert res.min_shots_per_half == 50
