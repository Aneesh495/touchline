# Run index

Every meaningful run is recorded here with its question, model, seed, and metrics,
including runs that produced a null or negative result. These are CPU diagnostic
profile runs on synthetic data; they exercise the full protocol (seeds, splits,
bootstrap, proper scores) and are labelled synthetic. The full-scale campaign over
acquired real data is blocked on data and compute and is recorded as such in
`docs/BUILD_STATUS.md`.

Reproduce with:

```python
from touchline.experiments.campaign import run_xg_comparison, run_strength_uncertainty
run_xg_comparison()        # H1
run_strength_uncertainty() # Q3
```

## H1: neural vs tabular xG (held-out log loss, lower is better)

| run | model | seed | log loss | Brier | note |
|-----|-------|------|----------|-------|------|
| xg_logistic_s0 | logistic | 0 | 0.4798 | 0.1563 | 95% CI [0.445, 0.516] |
| xg_neural_s0 | neural | 0 | 0.5117 | 0.1649 | loss 0.688 -> 0.453 |
| xg_logistic_s1 | logistic | 1 | 0.4798 | 0.1563 | 95% CI [0.446, 0.517] |
| xg_neural_s1 | neural | 1 | 0.5067 | 0.1652 | loss 0.699 -> 0.449 |
| xg_logistic_s2 | logistic | 2 | 0.4798 | 0.1563 | 95% CI [0.450, 0.515] |
| xg_neural_s2 | neural | 2 | 0.4964 | 0.1600 | loss 0.698 -> 0.455 |

The neural model trains (its training loss falls from about 0.69 to about 0.45 in
every seed, confirming real gradient movement and learning) but it does not beat
the logistic baseline on the held-out set. The logistic log loss (0.480) sits below
the neural log loss in all three seeds and inside the logistic bootstrap interval.
On this data the extra capacity does not help; the relationship between the chosen
features and goals is close to linear in the logit. This is a null result for H1 at
diagnostic scale and is recorded as such.

## Q3: strength uncertainty vs forecast

| run | model | title prob (favourite) |
|-----|-------|------------------------|
| forecast_point | point estimate | 0.924 |
| forecast_correlated | correlated draws | 0.881 |

Introducing correlated per-season strength draws lowers the favourite's title
probability from 0.924 to 0.881 and spreads mass to other contenders. A point
estimate understates the uncertainty in a forecast; the correlated draw is the
honest representation.
