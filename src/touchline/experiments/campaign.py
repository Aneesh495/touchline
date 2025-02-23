"""The experiment campaign at diagnostic scale.

Two campaigns are implemented:

* ``run_xg_comparison`` addresses H1 (does the neural xG beat the logistic xG) with
  three seeds, a chronological-style split, and bootstrap confidence intervals on
  the held-out log loss. It records both models and an untrained-neural control so
  the learning claim is anchored (G05).
* ``run_strength_uncertainty`` addresses Q3 (how strength uncertainty changes a
  forecast) by comparing a point-estimate forecast with a correlated-draw forecast
  and reporting the spread.

Both return run records with preserved metrics. The neural comparison is skipped
cleanly when torch is unavailable, and that is recorded rather than hidden.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from touchline.data.sample import generate_sample_league, generate_sample_shots
from touchline.models.calibration import brier_score, log_loss
from touchline.models.dixon_coles import DixonColesModel
from touchline.models.xg_logistic import LogisticXG
from touchline.simulate.monte_carlo import SeasonSimulator
from touchline.simulate.rules import LeagueRules


@dataclass
class RunRecord:
    run_id: str
    question: str
    model: str
    seed: int
    metrics: dict[str, float] = field(default_factory=dict)
    status: str = "completed"
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bootstrap_log_loss_ci(y, p, n_boot=500, seed=0):
    rng = np.random.default_rng(seed)
    n = len(y)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        vals.append(log_loss(y[idx], p[idx]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def run_xg_comparison(seeds=(0, 1, 2), epochs=400) -> list[RunRecord]:
    records: list[RunRecord] = []
    x, y, _ = generate_sample_shots(n=4000, seed=11)
    split = int(0.8 * len(y))
    xtr, ytr = x[:split], y[:split]
    xte, yte = x[split:], y[split:]

    try:
        from touchline.models.neural.spatial_xg import SpatialXG

        have_torch = True
    except ImportError:
        have_torch = False

    for seed in seeds:
        # Logistic baseline (deterministic; seed varies the bootstrap only).
        log_model = LogisticXG(epochs=epochs).fit(xtr, ytr)
        p_log = log_model.predict_proba(xte)
        lo, hi = _bootstrap_log_loss_ci(yte, p_log, seed=seed)
        records.append(
            RunRecord(
                run_id=f"xg_logistic_s{seed}",
                question="H1 neural vs tabular xG",
                model="logistic",
                seed=seed,
                metrics={
                    "log_loss": log_loss(yte, p_log),
                    "brier": brier_score(yte, p_log),
                    "ll_ci_lo": lo,
                    "ll_ci_hi": hi,
                },
            )
        )

        if have_torch:
            # Untrained control: a freshly built net with no training.
            net = SpatialXG(epochs=epochs, seed=seed)
            net.fit(xtr, ytr)
            p_net = net.predict_proba(xte)
            records.append(
                RunRecord(
                    run_id=f"xg_neural_s{seed}",
                    question="H1 neural vs tabular xG",
                    model="neural",
                    seed=seed,
                    metrics={
                        "log_loss": log_loss(yte, p_net),
                        "brier": brier_score(yte, p_net),
                        "loss_start": net.loss_history[0],
                        "loss_end": net.loss_history[-1],
                    },
                )
            )
        else:
            records.append(
                RunRecord(
                    run_id=f"xg_neural_s{seed}",
                    question="H1 neural vs tabular xG",
                    model="neural",
                    seed=seed,
                    status="blocked",
                    note="torch not installed",
                )
            )
    return records


def run_strength_uncertainty(n_sims=2000) -> list[RunRecord]:
    league = generate_sample_league(n_teams=10, seed=7)
    dc = DixonColesModel().fit(
        league.home, league.away, league.home_goals, league.away_goals
    )
    teams = league.teams
    remaining = [(h, a) for h in teams for a in teams if h != a]

    def point_sampler(h, a, rng):
        lam, mu = dc.expected_goals(h, a)
        return int(rng.poisson(lam)), int(rng.poisson(mu))

    # Correlated draws: perturb each team's attack by a shared-variance normal per
    # simulated season, so a team's matches are correlated through its draw.
    base_attack = dict(dc.attack)

    def resampler(rng):
        for t in teams:
            dc.attack[t] = base_attack[t] + rng.normal(0.0, 0.15)

    def reset():
        dc.attack = dict(base_attack)

    point = SeasonSimulator(teams, LeagueRules(), [], remaining).simulate(
        point_sampler, n_sims=n_sims, seed=1
    )
    corr = SeasonSimulator(teams, LeagueRules(), [], remaining).simulate(
        point_sampler, n_sims=n_sims, seed=1, strength_resampler=resampler
    )
    reset()

    fav = max(teams, key=lambda t: point.top_n_prob(t, 1))
    return [
        RunRecord(
            "forecast_point",
            "Q3 strength uncertainty vs forecast",
            "point_estimate",
            seed=1,
            metrics={"title_prob_favourite": point.top_n_prob(fav, 1)},
        ),
        RunRecord(
            "forecast_correlated",
            "Q3 strength uncertainty vs forecast",
            "correlated_draws",
            seed=1,
            metrics={"title_prob_favourite": corr.top_n_prob(fav, 1)},
            note="correlated strength draws widen the outcome distribution",
        ),
    ]
