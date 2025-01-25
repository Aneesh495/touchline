"""The bundled end-to-end demonstration.

The demo runs the whole spine on deterministic synthetic data so a fresh reader
sees, without any download:

1. a shot turning into an xG value (logistic model fit, then one shot scored),
2. a league fitted with Dixon-Coles and Elo,
3. the remaining season simulated into a table forecast with Monte Carlo error.

The data is clearly synthetic. The point is to exercise real code paths, not to
report a scientific result.
"""

from __future__ import annotations

import io

import numpy as np

from touchline.data.sample import generate_sample_league, generate_sample_shots
from touchline.models.calibration import brier_score, log_loss
from touchline.models.dixon_coles import DixonColesModel
from touchline.models.elo import EloModel
from touchline.models.xg_logistic import LogisticXG
from touchline.simulate.monte_carlo import SeasonSimulator
from touchline.simulate.rules import LeagueRules


def run_demo(out: io.TextIOBase | None = None, n_sims: int = 2000) -> dict:
    """Run the demo, print a report, and return a dict of key numbers."""
    import sys

    out = out or sys.stdout
    report: dict = {}

    def p(line: str = "") -> None:
        print(line, file=out)

    p("Touchline demo (synthetic sample data)")
    p("=" * 48)

    # 1. xG
    x, y, _ = generate_sample_shots(n=4000, seed=11)
    split = int(0.8 * len(y))
    xg = LogisticXG(epochs=500).fit(x[:split], y[:split])
    proba = xg.predict_proba(x[split:])
    ll = log_loss(y[split:], proba)
    bs = brier_score(y[split:], proba)
    # baseline: always predict the training base rate
    base = np.full(len(y) - split, y[:split].mean())
    ll_base = log_loss(y[split:], base)
    p("")
    p("1) Expected goals")
    p(f"   trained log loss {ll:.4f} vs base-rate {ll_base:.4f} (lower is better)")
    p(f"   trained Brier    {bs:.4f}")
    # Score one example shot: 8 m, decent angle, open play
    one = xg.predict_proba([[8.0, 0.9, 0, 0, 0, 0, 0]])[0]
    p(f"   example shot (8 m, open angle) xG = {one:.3f}")
    report["xg_log_loss"] = ll
    report["xg_log_loss_base"] = ll_base
    report["xg_example"] = float(one)

    # 2. League models
    league = generate_sample_league(n_teams=10, seed=7)
    dc = DixonColesModel().fit(
        league.home, league.away, league.home_goals, league.away_goals
    )
    elo = EloModel()
    for h, a, hg, ag in zip(
        league.home, league.away, league.home_goals, league.away_goals, strict=True
    ):
        elo.update(h, a, hg, ag)
    strongest = max(dc.attack, key=dc.attack.get)
    p("")
    p("2) Team strength")
    p(f"   Dixon-Coles home advantage (log) {dc.home_adv:+.3f}, rho {dc.rho:+.3f}")
    p(f"   strongest attack: {strongest} (attack {dc.attack[strongest]:+.3f})")
    report["dc_home_adv"] = dc.home_adv
    report["strongest_team"] = strongest

    # 3. Simulate a fresh season from the fitted Dixon-Coles model
    teams = league.teams
    remaining = [(h, a) for h in teams for a in teams if h != a]
    rules = LeagueRules()

    def sampler(h: str, a: str, rng: np.random.Generator) -> tuple[int, int]:
        lam, mu = dc.expected_goals(h, a)
        return int(rng.poisson(lam)), int(rng.poisson(mu))

    sim = SeasonSimulator(teams=teams, rules=rules, played_fixtures=[], remaining=remaining)
    result = sim.simulate(sampler, n_sims=n_sims, seed=1)
    p("")
    p(f"3) Simulated season ({n_sims} draws), title probabilities")
    title_probs = sorted(
        ((t, result.top_n_prob(t, 1)) for t in teams), key=lambda kv: -kv[1]
    )
    for t, prob in title_probs[:5]:
        se = result.monte_carlo_se(prob)
        p(f"   {t:10s} P(1st) = {prob:5.3f} +/- {se:5.3f}")
    report["title_favourite"] = title_probs[0][0]
    report["title_prob"] = title_probs[0][1]

    # Sanity: title favourite should be among the strong teams
    # Example head-to-head from the fitted model: strongest vs weakest team.
    weakest = min(dc.attack, key=dc.attack.get)
    ph, pd, pa = dc.result_probs(strongest, weakest)
    p("")
    p(f"   {strongest} vs {weakest}: "
      f"home {ph:.2f} / draw {pd:.2f} / away {pa:.2f}")
    report["h2h_strong_home_win"] = ph
    p("")
    p("Done. All numbers above come from fitted models on synthetic data.")
    return report
