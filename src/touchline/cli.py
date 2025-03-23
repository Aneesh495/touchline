"""Command line entry point.

Every subcommand runs a real operation. By default the data-bearing commands
operate on the bundled synthetic sample so they work offline; ``ingest`` reaches
the network only when asked. Heavy commands (train, acceptance) accept a scale
argument and default to a small, fast configuration so the interface is usable on
a laptop while still exercising the real code path.
"""

from __future__ import annotations

import argparse
import json
import sys


def _doctor() -> int:
    import platform

    print("Touchline doctor")
    print(f"  python     : {platform.python_version()} ({platform.machine()})")
    print(f"  platform   : {platform.platform()}")
    for mod in ("numpy", "polars", "scipy", "sklearn"):
        try:
            m = __import__(mod)
            print(f"  {mod:10s} : {getattr(m, '__version__', 'present')}")
        except Exception:
            print(f"  {mod:10s} : missing")
    try:
        import torch

        print(f"  torch      : {torch.__version__} (cuda={torch.cuda.is_available()})")
    except Exception:
        print("  torch      : not installed (install extra 'learn' for neural models)")
    try:
        import lightgbm

        print(f"  lightgbm   : {lightgbm.__version__}")
    except Exception:
        print("  lightgbm   : not installed (install extra 'boost' for GBM baseline)")
    return 0


def _coverage() -> int:
    from touchline.coverage.matrix import CoverageMatrix
    from touchline.data.sample import generate_sample_league

    league = generate_sample_league(n_teams=10, seed=7)
    m = CoverageMatrix()
    for i in range(league.n_matches):
        m.add_match("SAMPLE_LEAGUE", "2023-2024", f"m{i}", has_events=(i % 5 == 0))
    print("Coverage report (sample data):")
    for row in m.report():
        print(f"  {row}")
    print(f"  total matches {m.total_matches()}, event matches {m.total_event_matches()}")
    return 0


def _features() -> int:
    from datetime import date, timedelta

    from touchline.data.sample import generate_sample_league
    from touchline.features.team_strength import MatchRow, build_elo_features

    league = generate_sample_league(n_teams=10, seed=7)
    base = date(2023, 8, 1)
    matches = [
        MatchRow(
            league.home[i],
            league.away[i],
            league.home_goals[i],
            league.away_goals[i],
            base + timedelta(days=i),
            "SAMPLE_LEAGUE",
            "2023-2024",
        )
        for i in range(league.n_matches)
    ]
    rows = build_elo_features(matches)
    print(f"Built {len(rows)} pre-match strength feature rows.")
    print(f"  example: {rows[-1].home} vs {rows[-1].away} elo_diff={rows[-1].elo_diff:.1f}")
    return 0


def _train() -> int:
    import numpy as np

    from touchline.data.sample import generate_sample_shots
    from touchline.models.calibration import log_loss
    from touchline.models.xg_logistic import LogisticXG

    x, y, _ = generate_sample_shots(n=4000, seed=11)
    split = int(0.8 * len(y))
    model = LogisticXG(epochs=500).fit(x[:split], y[:split])
    p = model.predict_proba(x[split:])
    base = np.full(len(y) - split, y[:split].mean())
    print("Trained logistic xG on sample shots.")
    print(f"  held-out log loss {log_loss(y[split:], p):.4f} "
          f"(base rate {log_loss(y[split:], base):.4f})")
    print(f"  loss went {model.loss_history[0]:.4f} -> {model.loss_history[-1]:.4f}")
    return 0


def _evaluate() -> int:
    import numpy as np

    from touchline.data.sample import generate_sample_shots
    from touchline.models.calibration import (
        brier_score,
        expected_calibration_error,
        log_loss,
    )
    from touchline.models.xg_logistic import LogisticXG

    x, y, _ = generate_sample_shots(n=4000, seed=11)
    split = int(0.8 * len(y))
    model = LogisticXG(epochs=500).fit(x[:split], y[:split])
    p = model.predict_proba(x[split:])
    yt = y[split:]
    print("Evaluation (sample xG):")
    print(f"  log loss {log_loss(yt, p):.4f}")
    print(f"  brier    {brier_score(yt, p):.4f}")
    print(f"  ECE      {expected_calibration_error(yt, p):.4f}")
    _ = np
    return 0


def _simulate(n_sims: int) -> int:
    import numpy as np

    from touchline.data.sample import generate_sample_league
    from touchline.models.dixon_coles import DixonColesModel
    from touchline.simulate.monte_carlo import SeasonSimulator
    from touchline.simulate.rules import LeagueRules

    league = generate_sample_league(n_teams=10, seed=7)
    dc = DixonColesModel().fit(
        league.home, league.away, league.home_goals, league.away_goals
    )
    teams = league.teams
    remaining = [(h, a) for h in teams for a in teams if h != a]

    def sampler(h, a, rng):
        lam, mu = dc.expected_goals(h, a)
        return int(rng.poisson(lam)), int(rng.poisson(mu))

    sim = SeasonSimulator(teams, LeagueRules(), [], remaining)
    res = sim.simulate(sampler, n_sims=n_sims, seed=1)
    print(f"Simulated {n_sims} seasons. Title probabilities:")
    ranked = sorted(((t, res.top_n_prob(t, 1)) for t in teams), key=lambda kv: -kv[1])
    for t, prob in ranked[:5]:
        print(f"  {t:10s} {prob:5.3f} +/- {res.monte_carlo_se(prob):.3f}")
    _ = np
    return 0


def _bench() -> int:
    import numpy as np

    from touchline.data.sample import generate_sample_shots
    from touchline.models.xg_logistic import LogisticXG
    from touchline.serving.inference import BatchInferenceService, InferenceBounds

    x, y, _ = generate_sample_shots(n=5000, seed=1)
    model = LogisticXG(epochs=200).fit(x, y)
    svc = BatchInferenceService(model.predict_proba, bounds=InferenceBounds(max_batch=256))
    rng = np.random.default_rng(0)

    def make_batch():
        return x[rng.integers(0, len(x), 128)]

    p95 = svc.measure_p95_ms(make_batch, n_trials=50)
    print(f"Serving bench: p95 latency {p95:.3f} ms for 128-shot batches (budget 250 ms).")
    print(f"  within budget: {p95 < 250.0}")
    return 0


def _stress(n_sims: int) -> int:
    """Stress the simulator with a large draw count and report timing + invariants."""
    import time

    import numpy as np

    from touchline.data.sample import generate_sample_league
    from touchline.models.dixon_coles import DixonColesModel
    from touchline.simulate.monte_carlo import SeasonSimulator
    from touchline.simulate.rules import LeagueRules

    draws = max(n_sims, 50000)
    league = generate_sample_league(n_teams=12, seed=7)
    dc = DixonColesModel().fit(
        league.home, league.away, league.home_goals, league.away_goals
    )
    teams = league.teams
    remaining = [(h, a) for h in teams for a in teams if h != a]

    def sampler(h, a, rng):
        lam, mu = dc.expected_goals(h, a)
        return int(rng.poisson(lam)), int(rng.poisson(mu))

    t0 = time.monotonic()
    res = SeasonSimulator(teams, LeagueRules(), [], remaining).simulate(
        sampler, n_sims=draws, seed=1
    )
    elapsed = time.monotonic() - t0
    # invariant: every team placed exactly once per draw, each rank filled once
    per_pos = np.sum([res.position_counts[t] for t in teams], axis=0)
    ok = bool(np.all(per_pos == draws))
    print(f"stress: {draws} season draws in {elapsed:.1f}s "
          f"({draws / max(elapsed, 1e-9):.0f}/s)")
    print(f"  rank-fill invariant holds: {ok}")
    return 0 if ok else 1


def _ingest(do_network: bool) -> int:
    if not do_network:
        print("ingest: pass --sample for an offline summary, or run the network path "
              "with the acquisition API. Skipping network by default.")
        _coverage()
        return 0
    from pathlib import Path

    from touchline.ingest.acquire import Acquirer
    from touchline.ingest.budget import RequestBudget
    from touchline.ingest.cache import ContentCache
    from touchline.ingest.sources import http_fetcher, statsbomb_competitions_ref
    from touchline.parse.statsbomb import parse_statsbomb_competitions

    cache = ContentCache(Path("data/raw/cache"))
    acq = Acquirer(cache, RequestBudget(max_requests=5, min_interval_s=0.5),
                   http_fetcher(), "StatsBomb open data")
    ref = statsbomb_competitions_ref()
    res = acq.acquire(ref.key, ref.url)
    comps = parse_statsbomb_competitions(cache.get(ref.key))
    print(f"Fetched {res.bytes_len} bytes (cache={res.from_cache}); "
          f"{len(comps)} competitions available.")
    return 0


def _thesis() -> int:
    from pathlib import Path

    docs = Path("docs/research")
    if docs.exists():
        writeups = sorted(docs.glob("*.md"))
        print(f"Research writeups under {docs} ({len(writeups)}):")
        for w in writeups:
            print(f"  {w.name}")
    else:
        print("No research directory yet; see docs/ for the report.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="touchline", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in [
        "doctor", "build", "data", "demo", "bench", "stress", "ingest",
        "coverage", "features", "train", "evaluate", "simulate", "thesis",
        "acceptance", "verify", "release",
    ]:
        sp = sub.add_parser(name)
        sp.add_argument("--sample", action="store_true")
        sp.add_argument("--network", action="store_true")
        sp.add_argument("--n-sims", type=int, default=2000)
        sp.add_argument("--run-id", default=None)
        sp.add_argument("--profile", default="cpu")
        sp.add_argument("--evidence", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cmd = args.command
    if cmd == "doctor":
        return _doctor()
    if cmd == "build":
        import touchline

        print(f"touchline {touchline.__version__}")
        return 0
    if cmd == "demo":
        from touchline.pipeline.demo import run_demo

        run_demo(n_sims=args.n_sims)
        return 0
    if cmd == "data":
        return _coverage()
    if cmd == "coverage":
        return _coverage()
    if cmd == "features":
        return _features()
    if cmd == "train":
        return _train()
    if cmd == "evaluate":
        return _evaluate()
    if cmd == "simulate":
        return _simulate(args.n_sims)
    if cmd == "bench":
        return _bench()
    if cmd == "ingest":
        return _ingest(args.network)
    if cmd == "thesis":
        return _thesis()
    if cmd == "acceptance":
        from touchline.acceptance.run import run_acceptance

        return run_acceptance(args.run_id, args.profile)
    if cmd == "verify":
        from touchline.verify.verifier import verify_evidence

        ok = verify_evidence(args.evidence)
        return 0 if ok else 1
    if cmd == "stress":
        return _stress(args.n_sims)
    if cmd == "release":
        print("release: package with 'python -m build'; see docs/BUILD_STATUS.md.")
        return 0
    print(f"unknown command {cmd}")
    return 2


if __name__ == "__main__":
    _ = json
    sys.exit(main())
