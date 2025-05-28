"""Real-data xG campaign on acquired StatsBomb shots.

Runs one model family per invocation (``--model logistic|boosted|neural``) so torch
and lightgbm never load in the same process (their OpenMP runtimes deadlock on this
host). Builds the shot feature set from cached La Liga event matches, splits
chronologically by season, fits across three seeds, and appends its runs to a shared
JSON run index. A final ``--merge`` pass prints the combined table.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from touchline.models.calibration import brier_score, log_loss
from touchline.pipeline.statsbomb_pipeline import build_from_cache

CACHE = Path("data/raw/cache")
OUT = Path("docs/research/real_run_index.json")
SEASONS = [
    (11, 41, "LALIGA", "2008-2009"),
    (11, 21, "LALIGA", "2009-2010"),
    (11, 22, "LALIGA", "2010-2011"),
    (11, 23, "LALIGA", "2011-2012"),
    (11, 24, "LALIGA", "2012-2013"),
    (11, 25, "LALIGA", "2013-2014"),
    (11, 26, "LALIGA", "2014-2015"),
    (11, 27, "LALIGA", "2015-2016"),
    (11, 2, "LALIGA", "2016-2017"),
    (11, 1, "LALIGA", "2017-2018"),
    (11, 4, "LALIGA", "2018-2019"),
    (11, 42, "LALIGA", "2019-2020"),
    (11, 90, "LALIGA", "2020-2021"),
]


def _load():
    xs, ys, meta = [], [], []
    for cid, sid, code, season in SEASONS:
        try:
            res = build_from_cache(CACHE, cid, sid, code, season)
        except FileNotFoundError:
            continue
        if len(res.labels) == 0:
            continue
        xs.append(res.features)
        ys.append(res.labels)
        meta.append((season, len(res.labels)))
    return xs, ys, meta


def _splits(xs, ys):
    test_x, test_y = xs[-1], ys[-1]
    val_x, val_y = xs[-2], ys[-2]
    tr_x = np.vstack(xs[:-2])
    tr_y = np.concatenate(ys[:-2])
    return tr_x, tr_y, val_x, val_y, test_x, test_y


def _bootstrap_ci(y, p, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    vals = [log_loss(y[idx], p[idx]) for idx in
            (rng.integers(0, len(y), len(y)) for _ in range(n_boot))]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def _append_runs(new_runs, meta, total_shots):
    data = {"dataset": "statsbomb_laliga_real", "seasons": meta,
            "total_shots": total_shots, "test_season": SEASONS[-1][3], "runs": []}
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text())
        except json.JSONDecodeError:
            pass
    existing = {r["run_id"] for r in data.get("runs", [])}
    for r in new_runs:
        if r["run_id"] not in existing:
            data.setdefault("runs", []).append(r)
    data["seasons"] = meta
    data["total_shots"] = total_shots
    OUT.write_text(json.dumps(data, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["logistic", "boosted", "neural", "merge"], required=True)
    args = ap.parse_args()

    if args.model == "merge":
        data = json.loads(OUT.read_text())
        print(f"dataset={data['dataset']} total_shots={data['total_shots']} "
              f"test_season={data['test_season']}", flush=True)
        for r in sorted(data["runs"], key=lambda r: r["run_id"]):
            if "log_loss" in r:
                print(f"  {r['run_id']:14s} {r['model']:9s} "
                      f"ll={r['log_loss']:.4f} brier={r.get('brier', float('nan')):.4f}", flush=True)
            else:
                print(f"  {r['run_id']:14s} {r['model']:9s} {r.get('status')}", flush=True)
        return 0

    xs, ys, meta = _load()
    if len(xs) < 3:
        print("need >=3 cached seasons; run scripts/pull_campaign.py")
        return 1
    tr_x, tr_y, val_x, val_y, test_x, test_y = _splits(xs, ys)
    total = int(sum(len(y) for y in ys))
    print(f"model={args.model} seasons={len(xs)} shots={total} "
          f"train={len(tr_y)} test={len(test_y)} test_rate={test_y.mean():.4f}", flush=True)

    runs = []
    if args.model == "logistic":
        from touchline.models.xg_logistic import LogisticXG

        base = np.full(len(test_y), tr_y.mean())
        runs.append({"run_id": "base_rate", "model": "base_rate", "seed": 0,
                     "log_loss": log_loss(test_y, base), "brier": brier_score(test_y, base)})
        for seed in (0, 1, 2):
            m = LogisticXG(epochs=600).fit(tr_x, tr_y)
            p = m.predict_proba(test_x)
            runs.append({"run_id": f"logistic_s{seed}", "model": "logistic", "seed": seed,
                         "log_loss": log_loss(test_y, p), "brier": brier_score(test_y, p),
                         "ll_ci": _bootstrap_ci(test_y, p, seed=seed)})
    elif args.model == "boosted":
        from touchline.models.xg_boosted import BoostedXG

        for seed in (0, 1, 2):
            gbm = BoostedXG(n_estimators=300, seed=seed).fit(tr_x, tr_y, val_x, val_y)
            p = gbm.predict_proba(test_x)
            runs.append({"run_id": f"boosted_s{seed}", "model": "boosted", "seed": seed,
                         "log_loss": log_loss(test_y, p), "brier": brier_score(test_y, p),
                         "best_iteration": int(gbm.best_iteration)})
    elif args.model == "neural":
        from touchline.models.neural.spatial_xg import SpatialXG

        for seed in (0, 1, 2):
            net = SpatialXG(epochs=400, seed=seed).fit(tr_x, tr_y)
            p = net.predict_proba(test_x)
            runs.append({"run_id": f"neural_s{seed}", "model": "neural", "seed": seed,
                         "log_loss": log_loss(test_y, p), "brier": brier_score(test_y, p),
                         "loss_start": net.loss_history[0], "loss_end": net.loss_history[-1]})

    _append_runs(runs, meta, total)
    for r in runs:
        print(f"  {r['run_id']:14s} ll={r['log_loss']:.4f} brier={r['brier']:.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
