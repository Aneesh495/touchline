"""Baseline model oracles: Elo, Dixon-Coles, logistic xG, calibration.

Where a model is stochastic or data-driven, the test builds a known-truth dataset
and checks the model recovers the qualitative truth, rather than restating the
implementation.
"""

import numpy as np

from touchline.models.calibration import (
    PlattCalibrator,
    brier_score,
    expected_calibration_error,
    log_loss,
    reliability_table,
)
from touchline.models.dixon_coles import DixonColesModel
from touchline.models.elo import EloModel
from touchline.models.xg_logistic import LogisticXG


def test_elo_probs_sum_to_one_and_favour_stronger():
    elo = EloModel()
    elo.ratings = {"strong": 1800.0, "weak": 1400.0}
    ph, pd, pa = elo.predict_result_probs("strong", "weak")
    assert abs(ph + pd + pa - 1.0) < 1e-9
    assert ph > pa


def test_elo_updates_move_ratings_toward_result():
    elo = EloModel(k=20.0)
    before = elo.rating("A")
    elo.update("A", "B", home_goals=3, away_goals=0)
    assert elo.rating("A") > before  # winner's rating rises
    assert elo.rating("B") < 1500.0


def test_elo_margin_scales_update():
    big = EloModel(k=20.0, use_goal_margin=True)
    small = EloModel(k=20.0, use_goal_margin=True)
    big.update("A", "B", 4, 0)
    small.update("A", "B", 1, 0)
    assert big.rating("A") > small.rating("A")


def _simulate_league(rng, teams, strengths, home_adv=0.3):
    H, A, HG, AG = [], [], [], []
    for h in teams:
        for a in teams:
            if h == a:
                continue
            lam = np.exp(0.0 + home_adv + strengths[h] - (-strengths[a]))
            mu = np.exp(0.0 + strengths[a] - (-strengths[h]))
            H.append(h)
            A.append(a)
            HG.append(int(rng.poisson(lam)))
            AG.append(int(rng.poisson(mu)))
    return H, A, HG, AG


def test_dixon_coles_recovers_attack_ordering():
    rng = np.random.default_rng(0)
    teams = ["T0", "T1", "T2", "T3", "T4"]
    # strengths increasing with index
    strengths = {t: 0.3 * i - 0.6 for i, t in enumerate(teams)}
    # replicate the season several times for a stable fit
    H, A, HG, AG = [], [], [], []
    for _ in range(8):
        h, a, hg, ag = _simulate_league(rng, teams, strengths)
        H += h
        A += a
        HG += hg
        AG += ag
    m = DixonColesModel().fit(H, A, HG, AG)
    assert m.fitted
    # The strongest team should have the highest attack estimate.
    best = max(m.attack, key=m.attack.get)
    assert best == "T4"
    ph, pd, pa = m.result_probs("T4", "T0")
    assert abs(ph + pd + pa - 1.0) < 1e-6
    assert ph > pa  # strong home team favoured


def test_xg_logistic_learns_distance_effect():
    rng = np.random.default_rng(1)
    n = 4000
    dist = rng.uniform(1, 35, n)
    angle = rng.uniform(0.05, 1.2, n)
    extra = np.zeros((n, 5))
    x = np.column_stack([dist, angle, extra])
    # true goal prob decreases with distance, increases with angle
    logit = 2.0 - 0.15 * dist + 1.5 * angle
    p = 1.0 / (1.0 + np.exp(-logit))
    y = (rng.uniform(size=n) < p).astype(float)
    model = LogisticXG(epochs=600, lr=0.5)
    model.fit(x, y)
    # loss decreased over training
    assert model.loss_history[-1] < model.loss_history[0]
    # gradient at init is nonzero (real learning signal)
    assert model.gradient_norm_at_init(x, y) > 1e-3
    # closer central shot predicted higher than far shot
    close = model.predict_proba([[6, 1.0, 0, 0, 0, 0, 0]])[0]
    far = model.predict_proba([[30, 0.2, 0, 0, 0, 0, 0]])[0]
    assert close > far


def test_proper_scores_and_reliability():
    y = np.array([0, 0, 1, 1, 1, 0, 1, 0])
    p = np.array([0.1, 0.2, 0.8, 0.7, 0.9, 0.3, 0.6, 0.4])
    assert 0 < log_loss(y, p) < 1.0
    assert 0 < brier_score(y, p) < 0.25
    table = reliability_table(y, p, bins=5)
    assert sum(b.count for b in table) == len(y)


def test_platt_improves_miscalibrated_probs():
    rng = np.random.default_rng(2)
    n = 3000
    true_p = rng.uniform(0.05, 0.95, n)
    y = (rng.uniform(size=n) < true_p).astype(float)
    # overconfident raw probabilities pushed toward extremes
    raw = np.clip(true_p ** 0.5, 1e-3, 1 - 1e-3)
    ece_before = expected_calibration_error(y, raw)
    cal = PlattCalibrator().fit(raw, y)
    ece_after = expected_calibration_error(y, cal.transform(raw))
    assert ece_after <= ece_before + 1e-6
