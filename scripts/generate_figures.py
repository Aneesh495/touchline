"""Generate research figures from frozen artifacts into docs/research/figures.

Runs the diagnostic campaign, builds a reliability diagram for the logistic xG and
a title-probability bar chart from the simulator, and writes them as SVG with the
run id embedded. Deterministic, so the figures correspond to exact runs.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from touchline.data.sample import generate_sample_league, generate_sample_shots
from touchline.figures.svg_charts import bar_chart_svg, reliability_diagram_svg
from touchline.models.calibration import reliability_table
from touchline.models.dixon_coles import DixonColesModel
from touchline.models.xg_logistic import LogisticXG
from touchline.simulate.monte_carlo import SeasonSimulator
from touchline.simulate.rules import LeagueRules


def main() -> None:
    out = Path("docs/research/figures")
    out.mkdir(parents=True, exist_ok=True)

    # Reliability diagram for the logistic xG.
    x, y, _ = generate_sample_shots(n=4000, seed=11)
    split = int(0.8 * len(y))
    model = LogisticXG(epochs=500).fit(x[:split], y[:split])
    p = model.predict_proba(x[split:])
    table = reliability_table(y[split:], p, bins=10)
    svg = reliability_diagram_svg(
        [b.mean_prediction if b.count else 0.0 for b in table],
        [b.observed_rate if b.count else 0.0 for b in table],
        [b.count for b in table],
        run_id="xg_logistic (sample seed=11)",
    )
    (out / "xg_reliability.svg").write_text(svg)

    # Title-probability bar chart from the simulator.
    league = generate_sample_league(n_teams=10, seed=7)
    dc = DixonColesModel().fit(
        league.home, league.away, league.home_goals, league.away_goals
    )
    teams = league.teams
    remaining = [(h, a) for h in teams for a in teams if h != a]

    def sampler(h, a, rng):
        lam, mu = dc.expected_goals(h, a)
        return int(rng.poisson(lam)), int(rng.poisson(mu))

    res = SeasonSimulator(teams, LeagueRules(), [], remaining).simulate(
        sampler, n_sims=5000, seed=1
    )
    ranked = sorted(((t, res.top_n_prob(t, 1)) for t in teams), key=lambda kv: -kv[1])[:6]
    chart = bar_chart_svg(
        [t for t, _ in ranked],
        [v for _, v in ranked],
        run_id="forecast (DC sample, 5000 draws)",
    )
    (out / "title_probabilities.svg").write_text(chart)
    print("wrote", out / "xg_reliability.svg")
    print("wrote", out / "title_probabilities.svg")
    _ = np


if __name__ == "__main__":
    main()
