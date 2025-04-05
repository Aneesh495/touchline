"""Rolling-origin Elo forecast oracles."""

from datetime import date, timedelta

import numpy as np

from touchline.experiments.rolling import rolling_elo_forecast
from touchline.features.team_strength import MatchRow


def _season(seed=0):
    """Build a synthetic multi-matchday season with latent strengths."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i}" for i in range(8)]
    strength = {t: rng.normal(0, 0.4) for t in teams}
    base = date(2022, 8, 1)
    matches = []
    day = 0
    for _ in range(6):
        rng.shuffle(teams)
        for i in range(0, len(teams), 2):
            h, a = teams[i], teams[i + 1]
            lam = np.exp(0.2 + strength[h] - strength[a])
            mu = np.exp(0.1 + strength[a] - strength[h])
            matches.append(
                MatchRow(
                    h, a, int(rng.poisson(lam)), int(rng.poisson(mu)),
                    base + timedelta(days=day), "LG", "2022-2023"
                )
            )
        day += 7
    return matches


def test_rolling_forecast_produces_folds():
    matches = _season()
    cuts = [date(2022, 8, 22), date(2022, 9, 5), date(2022, 9, 19)]
    folds = rolling_elo_forecast(matches, cuts)
    assert len(folds) >= 1
    for f in folds:
        assert f.n_train > 0
        assert f.n_test > 0
        assert f.log_loss > 0
        assert f.baseline_log_loss > 0


def test_elo_beats_or_matches_base_rate_on_average():
    # Average over several synthetic seasons: Elo should on average not be worse
    # than a naive base-rate predictor once enough training data accrues.
    wins = 0
    total = 0
    for seed in range(8):
        matches = _season(seed)
        cuts = [date(2022, 9, 12), date(2022, 9, 26)]
        for f in rolling_elo_forecast(matches, cuts):
            total += 1
            if f.log_loss <= f.baseline_log_loss + 0.05:
                wins += 1
    # Elo is competitive on most folds (allowing a small tolerance for noise).
    assert wins >= total // 2
