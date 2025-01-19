# Touchline

Touchline is a football research platform that connects match outcomes, on-ball
events, available spatial context, player roles, and competition simulations
across the five major European leagues and the UEFA Champions League.

The focus is football's continuous spatial action: possession value, the worth of
an action given where and when it happens, role-dependent contribution, and how a
season's structure turns team strength into a table forecast. This is deliberately
not a general statistics dump. Every measure is defined, every model owns its
target, and the knowledge available at prediction time is respected so later facts
cannot leak into earlier forecasts.

## What is here

- A typed football domain core: matches, periods, possessions, events, shots,
  appearances, team and player identities, venues, score state, and
  competition-rule objects, with clocks that keep halves, extra time, stoppage
  time, and shootouts distinct.
- Parsers for real open datasets: the StatsBomb / Hudl open-data event schema and
  the football-data.co.uk historical results files.
- Original models with documented targets: Elo and Dixon-Coles score models, xG
  (logistic, gradient-boosted, and a small neural spatial model), a grid-based
  expected-threat solve, and a possession action-value model.
- A competition simulator with era-specific points, tie-breaks, and UCL formats.
- A chronological feature pipeline with a leakage audit.

## Quick start

```bash
make bootstrap      # create the environment and install the package
make doctor         # report host capabilities and data availability
make demo           # run the end-to-end vertical slice on bundled sample data
make test           # run the correctness suite
```

The demo runs without any download using a small bundled sample so a fresh reader
can see an event turn into an xG value and a set of team strengths turn into a
simulated table.

## Status

This repository is under active construction. `docs/BUILD_STATUS.md` tracks which
capabilities and acceptance gates are implemented, which are blocked on large data
or compute, and what evidence exists for each. Nothing here is presented as more
complete than it is.

## Layout

```
src/touchline/      domain core, parsers, features, models, simulator, serving
tests/              correctness, property, and differential tests
docs/               architecture, specification, research writeups, diagrams
data/sample/        tiny committed sample for the demo
```

## License and attribution

MIT. Dataset licenses are the responsibility of the data provider; see
`docs/DATASETS.md`. The action-value formulation draws on Decroos et al.,
"Actions Speak Louder than Goals" (KDD 2019) as a reference for the idea of
valuing actions by their effect on scoring and conceding probability.
