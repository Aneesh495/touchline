# Expected goals: geometry, calibration, and whether non-linearity helps

## Question

Can a tabular logistic model of shot geometry and situation produce well-calibrated
expected goals, and does a neural model on the same inputs do better?

## Related work

The expected-goals idea values a shot by its scoring probability given context.
Distance and the angle subtended by the goal mouth are the canonical geometric
features. The action-value literature (Decroos et al., KDD 2019) builds on xG by
valuing every action, not only shots.

## Data and eligibility

Diagnostic profile: 4,000 synthetic shots generated with a known logit that falls
with distance and rises with angle, plus a penalty bump (`data.sample`). Penalties
and shootout kicks are separable; shootout kicks never enter regulation xG. The
full profile uses the StatsBomb open-data shots.

## Definitions

`xg` is the modelled goal probability per shot. Features are distance (m), angle
(rad), header, penalty, free kick, corner, and counter indicators. Standardisation
uses training statistics only.

## Model

Logistic xG: P(goal) = sigmoid(w·x + b), fit by weighted gradient descent
(`models.xg_logistic`). Neural xG: a 32-16 MLP on the same features
(`models.neural.spatial_xg`). Calibration by validation-only Platt scaling with
reliability tables and ECE (`models.calibration`).

## Experiment

Three seeds, 80/20 chronological-style split, bootstrap confidence intervals on the
held-out log loss (`experiments.campaign.run_xg_comparison`).

## Result

| model | log loss | Brier |
|-------|----------|-------|
| logistic | 0.480 | 0.156 |
| neural (seed 0/1/2) | 0.512 / 0.507 / 0.496 | 0.165 / 0.165 / 0.160 |

The neural model trains (loss 0.69 to 0.45 each seed) but does not beat the
logistic baseline; the logistic log loss sits below the neural in every seed and
inside its own bootstrap interval [0.445, 0.517]. On this data the logit is close
to linear, so the extra capacity adds variance without reducing bias.

## Sensitivity and negative cases

The result is stable across seeds. It is specific to these features: with real
spatial context (defender positions via the set encoder) the relationship may
become non-linear enough for the neural model to win, which is the full-profile
test.

## Conclusion

A linear xG is a strong, well-calibrated baseline here. H1 is a null result at
diagnostic scale (see `NEGATIVE_RESULTS.md`). The claim that spatial context helps
is unproven until the real-data campaign runs.
