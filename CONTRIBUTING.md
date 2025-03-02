# Contributing

Touchline is a research codebase; contributions should keep it honest and testable.

## Setup

```bash
make bootstrap            # venv + install
uv pip install -e '.[learn,boost]'   # optional: neural and boosting models
make test                 # run the suite
make lint                 # ruff
```

## Principles

- Respect the layer boundaries (see `docs/ARCHITECTURE.md`); never import upward.
- A new feature carries its knowledge time; leakage is not acceptable.
- Models own their targets and training loops; add a learning check (loss falls,
  gradient moves) for any learned component.
- Tests reason the expected result independently of the implementation. Do not
  generate the expected output from the code under test.
- Label synthetic data as synthetic; never count it toward a real-data gate.
- Report discrepancies and null results; do not force agreement or hide nulls.

## Running tests reliably

Some sandboxes hang on the coverage plugin autoload. The `make test` target sets
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; use it if a bare `pytest` stalls.

## Commits

Keep commits focused on one reviewable change with its tests and a message that
explains the behaviour and the checks run.

## Writing

Public prose explains mechanisms, assumptions, and limitations. Avoid decorative
banners and comments that restate code. No em dashes.
