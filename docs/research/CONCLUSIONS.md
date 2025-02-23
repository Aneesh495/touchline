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
