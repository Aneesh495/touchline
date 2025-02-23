# Hypotheses

Each hypothesis has an operational definition, a minimum useful effect, the main
confounders, exclusions, how uncertainty is reported, and the criterion that would
count it as failed. Predictive and causal questions are kept distinct: most of
these are predictive, and the few that invite a causal reading are marked as not
identifiable from observational data alone.

The status column reflects what has been evaluated so far. On the CPU diagnostic
profile several are exercised on synthetic or small data; the full-scale evaluation
is blocked on data and compute (see `docs/BUILD_STATUS.md`). A null result is a
valid outcome and is reported as such.

| # | Hypothesis | Type | Minimum useful effect | Status |
|---|-----------|------|-----------------------|--------|
| H1 | A neural spatial/context xG beats a tabular logistic xG on held-out proper scores | predictive | log loss improvement beyond bootstrap noise | exercised (synthetic) |
| H2 | Finishing persists beyond xG (a player's goals minus xG is stable across splits) | predictive | positive split-half correlation with CI excluding 0 | planned |
| H3 | Passing accuracy and progressive value diverge (accurate passers are not always progressive) | predictive | rank correlation well below 1 | planned |
| H4 | Dribble risk and value depend on role | predictive | role interaction term with CI excluding 0 | planned |
| H5 | Corner and free-kick conversion is weakly repeatable | predictive | shrunk between-team variance small but positive | planned (rare-event) |
| H6 | Penalty conversion has taker and keeper effects beyond chance | predictive | hierarchical effect SD above 0 with CI | planned |
| H7 | A red card reduces the team's subsequent action value | predictive | negative post-dismissal effect with CI | planned |
| H8 | Fixture congestion is associated with reduced performance | predictive | negative rest-days coefficient; travel proxy flagged uncertain | planned |
| H9 | Hierarchical structure improves transfer to a held-out competition | predictive | lower held-out log loss than a pooled baseline | exercised (small) |
| H10 | Role/context-adjusted contribution reorders raw leaderboards | predictive | rank changes beyond shrinkage noise | exercised (shrinkage) |
| H11 | Transfer adaptation shows a settling period (post-transfer output trends toward prior level) | predictive, not causal | trend with CI; confounders noted | planned |
| H12 | Contract horizon is associated with transfer timing | predictive, not causal | association with censoring handled; no causal claim | planned |

## Confounders and exclusions (shared)

- Minutes selection: players with few minutes are excluded or shrunk.
- Team context: a player's output confounds with teammates and opponents; stated
  as a limitation wherever an individual effect is reported.
- Survivorship: aging and development studies account for players leaving the
  sample.
- Multiple comparisons: exploratory analyses are labelled separately from the
  three confirmatory questions and are not reported as confirmatory findings.

## Failure criteria

A hypothesis fails if its predeclared effect's confidence interval does not exclude
the null in the declared direction on the frozen holdout. Failure is reported in
`docs/research/NEGATIVE_RESULTS.md`, not hidden.
