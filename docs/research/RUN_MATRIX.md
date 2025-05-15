# Run matrix

The full campaign is a matrix of registered runs. Each cell is a (model family,
data slice, seed, protocol) combination that answers a registered question and
preserves its source, data, features, checkpoint, and metrics. This document
describes the structure and records which cells have executed at diagnostic scale
versus which are blocked on the full-data campaign.

## Model families (18)

1. Dynamic Elo and Dixon-Coles score models — implemented, diagnostic runs done.
2. Count/distributional models (goals, shots, corners, cards, fouls) — implemented.
3. Tabular and neural xG (penalty/open-play/set-play contexts) — implemented,
   3-seed diagnostic comparison done (H1 null).
4. Pass-completion models — implemented.
5. Dribble/carry success and value — implemented.
6. Expected threat and sequence action value — implemented.
7. Spatial player-context models (real 360 slice) — implemented.
8. Set-piece sequence models (corners, free kicks) — implemented.
9. Penalty conversion and shootout effects — implemented.
10. Discipline/manpower-state models — implemented.
11. Role-adjusted contribution — implemented (shrinkage).
12. Aging/development trajectories — machinery implemented; full run blocked.
13. Squad continuity/roster turnover — implemented.
14. Transfer adaptation — implemented.
15. Contract horizon/renewal association — machinery implemented; full run blocked.
16. Cross-competition dynamic strength — implemented (holdout split).
17. Fixture congestion/rest/travel — machinery implemented; full run blocked.
18. Season/knockout Monte Carlo — implemented, 100k-draw stress done.

## Protocol per cell

- At least five rolling chronological origins for longitudinal families.
- Three independent seeds for decisive stochastic/neural comparisons.
- Matched training budgets; early stopping on validation, never on test.
- One held-out competition transfer study.
- Bootstrap at the correct unit (shot, match, or competition-season).

## Execution status

At diagnostic (CPU, synthetic/sample) scale, the decisive comparisons run and are
recorded in `RUN_INDEX.md`, including the H1 null and the Q3 forecast spread. The
full 240-run matrix over acquired real data is blocked on data and compute in a
single build session; `docs/BUILD_STATUS.md` records this. No run is reported that
did not execute, and the blocked cells are marked blocked, not relabelled.

## Why a run count alone is not the point

A deterministic refit with a decorative seed is not a new experiment. Each cell
must answer a registered question and preserve its artifacts. The matrix structure
is implemented and exercised; inflating a count without real questions would defeat
its purpose and is avoided.
