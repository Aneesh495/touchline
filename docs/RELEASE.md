# Release and fresh-setup verification

How Touchline is packaged and how a fresh reader verifies it runs.

## Build

```bash
.venv/bin/python -m build
```

Produces `dist/touchline-0.1.0-py3-none-any.whl` and the sdist. The build is
hatchling-based and packages `src/touchline`.

## Fresh-setup verification

Verified this session in a clean isolated environment:

```bash
uv venv --python 3.12 /tmp/fresh
VIRTUAL_ENV=/tmp/fresh uv pip install dist/touchline-0.1.0-py3-none-any.whl
/tmp/fresh/bin/touchline build     # prints: touchline 0.1.0
/tmp/fresh/bin/touchline demo      # runs the full vertical slice
```

The `touchline` console entry point works from the installed wheel, and the demo
runs end to end (xG beats the base rate, the strongest fitted team is the title
favourite). This is the fresh-setup/demo part of the release gate.

## What remains for the full release gate

The full-profile acceptance campaign over acquired real data and the remote
publication of that evidence are blocked on data and compute in a single build
session. The code paths are implemented and tested at diagnostic scale; the
acceptance runner and verifier produce and check a complete evidence bundle. See
`docs/BUILD_STATUS.md` for the per-gate status.

## Optional extras

```bash
uv pip install -e '.[learn]'   # torch, for neural models
uv pip install -e '.[boost]'   # lightgbm, for the gradient-boosted xG
```

The core installs and runs without these; models that need them raise a clear
install hint rather than failing at import.
