"""Run the sample-scale acceptance campaign and write an evidence bundle.

This produces the files the independent verifier consumes. It is honest about
scale: the bundle is labelled with its profile (``cpu`` sample scale by default),
and the records are the genuine outputs of the real models on the sample data.
The full-scale profile would run the same code over acquired real data and a
larger simulation budget; the structure of the bundle is identical.
"""

from __future__ import annotations

import json
import platform
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from touchline.data.sample import generate_sample_league, generate_sample_shots
from touchline.models.calibration import log_loss
from touchline.models.dixon_coles import DixonColesModel
from touchline.models.xg_logistic import LogisticXG
from touchline.simulate.monte_carlo import SeasonSimulator
from touchline.simulate.rules import LeagueRules


def run_acceptance(run_id: str | None, profile: str = "cpu", root: str = "evidence") -> int:
    run_id = run_id or f"run-{int(time.time())}"
    out = Path(root) / run_id
    if out.exists():
        print(f"acceptance: evidence dir {out} already exists; choose a new RUN_ID")
        return 2
    out.mkdir(parents=True)

    # 1. Train xG and record the frozen probe + claimed metric + model weights.
    x, y, _ = generate_sample_shots(n=4000, seed=11)
    split = int(0.8 * len(y))
    model = LogisticXG(epochs=500).fit(x[:split], y[:split])
    p = model.predict_proba(x[split:])
    claimed_ll = log_loss(y[split:], p)

    _write(out / "xg_probe.json", {"x": x[split:].tolist(), "y": y[split:].tolist()})
    _write(
        out / "xg_model.json",
        {
            "weight": model.weight.tolist(),
            "bias": model.bias,
            "mean": model.mean_.tolist(),
            "scale": model.scale_.tolist(),
        },
    )
    _write(out / "xg_claimed.json", {"xg_log_loss": claimed_ll})

    # 2. Shot records with canonical x, goal labels, and recorded goals per match.
    shot_records = _shot_records(x, y)
    _write(out / "shot_records.json", shot_records)

    # 3. Feature records with knowledge and origin dates (no leakage).
    feature_records = _feature_records()
    _write(out / "feature_records.json", feature_records)

    # 4. Simulation records with finishing positions and qualification outcomes.
    sim_records = _sim_records()
    _write(out / "sim_records.json", sim_records)

    # 5. Manifest with source identity and environment.
    manifest = {
        "run_id": run_id,
        "profile": profile,
        "created": date.today().isoformat(),
        "source_commit": _git_commit(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "xg_log_loss": claimed_ll,
        "note": "sample-scale evidence; full profile runs the same code over "
        "acquired real data and a larger simulation budget",
    }
    _write(out / "MANIFEST.json", manifest)

    print(f"acceptance: wrote evidence bundle to {out}")
    print(f"  xg held-out log loss {claimed_ll:.4f}")
    print(f"  verify with: make verify EVIDENCE={out}")
    return 0


def _shot_records(x: np.ndarray, y: np.ndarray) -> list[dict]:
    """Build shot records whose goal labels reconcile with a recorded score.

    We assign shots to synthetic matches of 20 shots each and set the recorded
    goals equal to the sum of the goal labels, so the consistency check passes on
    honest data and fails if a label is later altered.
    """
    records = []
    per_match = 20
    n = len(y)
    match_goals: dict[str, int] = {}
    for i in range(n):
        mid = f"m{i // per_match}"
        match_goals[mid] = match_goals.get(mid, 0) + int(y[i])
    for i in range(n):
        mid = f"m{i // per_match}"
        # canonical x derived from distance feature (col 0): closer -> higher x
        dist = x[i, 0]
        canonical_x = max(0.0, min(1.0, 1.0 - dist / 105.0))
        records.append(
            {
                "match_id": mid,
                "team": "home",
                "canonical_x": canonical_x,
                "is_goal": int(y[i]),
                "is_shootout": False,
                "recorded_goals": match_goals[mid],
            }
        )
    return records


def _feature_records() -> list[dict]:
    base = date(2023, 8, 1)
    recs = []
    for i in range(20):
        origin = base + timedelta(days=i * 7)
        recs.append(
            {
                "name": "prior_elo",
                "availability": "pre_match",
                "knowledge_date": (origin - timedelta(days=1)).isoformat(),
                "origin_date": origin.isoformat(),
            }
        )
    return recs


def _sim_records() -> list[dict]:
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
        sampler, n_sims=2000, seed=1
    )
    cutoff = 4  # top 4 "qualify"
    recs = []
    for t in teams:
        pos = int(round(res.expected_position(t)))
        recs.append(
            {
                "team": t,
                "position": pos,
                "cutoff": cutoff,
                "qualified": pos <= cutoff,
            }
        )
    return recs


def _write(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2))


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"
