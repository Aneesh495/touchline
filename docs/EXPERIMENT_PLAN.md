# Experiment plan

This plan is frozen before final measurements. It separates a CPU diagnostic
profile (fast, runs on a laptop, used throughout development) from a full
acceptance profile (large acquired data and a bigger simulation budget).

## Endpoints

| Question | Primary metric | Unit of analysis | Decision rule |
|----------|----------------|------------------|---------------|
| Q1 spatial vs tabular action value | held-out log loss, Brier | shot | lower proper score with non-overlapping bootstrap CIs |
| Q2 hierarchical transfer | log loss on held-out competition | match | improvement over a pooled baseline with CI |
| Q3 strength uncertainty vs forecast | spread of qualification probability | competition-season | wider, calibrated intervals under correlated draws |

## Seeds and budgets

- Decisive stochastic/neural comparisons use at least three independent seeds.
- Training budgets are matched across compared models; early stopping is on
  validation loss, never on the test set.
- Longitudinal families use rolling chronological origins.

## Bootstrap

Uncertainty is bootstrapped at the correct unit: shots for xG, matches for score
models, competition-seasons for forecasts. Correlated events are never treated as
independent matches.

## Diagnostic (CPU) profile

- xG: 4,000 synthetic shots, 500 epochs, 80/20 chronological split.
- Score model: a 10-team synthetic double round-robin.
- Simulation: 2,000 season draws by default (`--n-sims` to raise).

This profile exists so every code path runs in seconds and the discipline (splits,
calibration, seeds, verification) is exercised end to end. Numbers from it are
clearly labelled synthetic and are not scientific claims.

## Full acceptance profile

The full profile runs the identical code over acquired real data:

- match-level results across the required competitions and seasons,
- the StatsBomb open-data event subset for event-level depth,
- a simulation budget of at least 100,000 draws per frozen showcase scenario.

The full profile is blocked in a single build session by acquisition volume and
compute; `docs/BUILD_STATUS.md` records it as blocked with the implemented lawful
acquisition path. No threshold is lowered and no smoke run is substituted for the
full campaign.

## Protocol changes

Any change to this protocol requires a new version of this document and a fresh
campaign; earlier results are retained, not overwritten.
