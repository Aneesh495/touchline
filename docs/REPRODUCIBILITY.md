# Reproducibility

How to reproduce every number in this repository from a clean checkout.

## Environment

```bash
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
uv pip install -e ".[learn,boost]"   # for neural and boosted models
```

Pinned to Python 3.12 (torch wheels available on aarch64). The core installs and
runs without the optional extras.

## Deterministic seeds

Every data generator and campaign takes an explicit seed. The demo, the campaign,
the figures, and the acceptance bundle all use fixed seeds (shots seed 11, league
seed 7, campaign seeds 0/1/2), so re-running produces identical numbers.

## Reproduce the headline results

```bash
make demo                    # the vertical slice
python -c "from touchline.experiments.campaign import run_xg_comparison as r; print([x.metrics for x in r()])"
make simulate N_SIMS=5000    # title probabilities
python scripts/generate_figures.py   # the report figures
```

The xG null result (logistic 0.480 vs neural 0.496-0.512) and the forecast spread
(0.924 point vs 0.881 correlated) reproduce exactly with these seeds.

## Reproduce the acceptance evidence and verify it

```bash
make acceptance RUN_ID=repro PROFILE=cpu
make verify EVIDENCE=evidence/repro
```

The verifier recomputes the semantic checks and replays the saved xG weights; it
passes a clean bundle and rejects any tampered copy (see
`tests/test_verifier_controls.py`).

## Reproduce the real-data path

```bash
python scripts/pull_statsbomb.py 11 90 LALIGA 2020-2021 30
python scripts/fit_real_xg.py
```

The first command fetches real StatsBomb open data (budgeted, cached, resumable);
the second fits xG on the real parsed shots. Counts (119,145 events from 30 matches)
are stable because the source is fixed.

## Tests

```bash
make test        # three isolated process groups (core, boosted, neural)
```

torch and lightgbm run in separate processes because their OpenMP runtimes conflict
in one interpreter on some hosts.
