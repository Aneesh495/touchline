# Conclusions

Each conclusion states its scope, its uncertainty, any counterexample, how robust
it is, and what additional evidence could overturn it. These conclusions are drawn
from the CPU diagnostic profile on synthetic data unless stated otherwise; the
full-scale conclusions await the blocked real-data campaign.

## C1: On these features, a linear xG is a strong baseline

Scope: synthetic shots with geometric and situation features.
Finding: the logistic xG matched or beat the neural xG on held-out log loss across
three seeds.
Uncertainty: bootstrap intervals on the logistic log loss were about [0.445, 0.517].
Counterexample: none observed on this data.
Robustness: consistent across all three seeds.
Overturned by: a real event-data campaign where spatial context makes the
relationship non-linear enough for the neural model to win.

## C2: Forecast uncertainty must include strength uncertainty

Scope: synthetic league simulation.
Finding: correlated per-season strength draws reduced the favourite's title
probability from 0.924 to 0.881 and spread mass to rivals.
Uncertainty: Monte Carlo standard errors are reported per probability.
Robustness: the direction (point estimate overstates confidence) is a structural
property, not a data artifact.
Overturned by: nothing expected; this is a methodological point confirmed by
construction.

## C3: The protocol catches leakage and tampering

Scope: the verifier and its negative controls.
Finding: the independent verifier rejects future-feature leakage, a flipped pitch,
altered goal labels, an impossible qualification, a tampered replay metric, and a
missing artifact, each by recomputation rather than a stored flag.
Robustness: the controls run the verifier as a subprocess on corrupted copies.
Overturned by: a control that the verifier fails to catch, which would be a defect
to fix.

## What remains open

The confirmatory evaluation of H1 and Q2 (hierarchical transfer) on real data, and
all of H2 through H12, are open pending the full-scale campaign. They are predeclared
in `HYPOTHESES.md` and will be reported with uncertainty whether positive or null.

## C4: On real shots, learned xG beats the base rate; boosting leads

Scope: 3,562 real StatsBomb La Liga shots, chronological split, test season
2020-2021 (839 shots).
Finding: logistic (0.364), gradient-boosted (0.351), and neural (0.363-0.390) xG
all beat the base-rate log loss (0.391) on the held-out season. The boosted model
is best; the neural MLP does not reliably beat the logistic baseline across seeds.
Uncertainty: the logistic held-out log loss carries a bootstrap interval in
`real_run_index.json`; the neural spread across seeds is the honest uncertainty on
that family.
Counterexample: the synthetic diagnostic data gave a neural null (C1); the real
data shows boosting winning, so the diagnostic null did not generalise to "no model
helps".
Robustness: consistent across the three seeds for the deterministic logistic and
boosted fits; neural varies.
Overturned by: a larger real-data campaign with per-shot spatial context (the set
encoder on 360 matches) where the neural family might overtake boosting.


## C5: The rules engine reproduces real league tables; Elo beats the base rate

Scope: 69 completed league seasons (five leagues, 2010-2024) from
football-data.co.uk results.
Finding: the rules engine reproduces the actual champions and standings from
official results (e.g. Man United 2010-11 at 80 pts, Real Madrid 2011-12 at 100
pts, Montpellier winning Ligue 1 2011-12, Dortmund's back-to-back Bundesligas),
matching the public historical record. A rolling-origin Elo result forecast beats
a base-rate predictor on held-out real matches in all five leagues (e.g. Serie A
1.020 vs 1.086 multiclass log loss).
Uncertainty: the forecast is a single train/test split per league; the numbers are
in `real_tables.json`.
Counterexample: none; every reproduced champion matches the record.
Overturned by: a reproduction that disagrees with an official final table, which
would indicate a rules or parsing bug.