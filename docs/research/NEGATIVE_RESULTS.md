# Negative and null results

These are kept deliberately, because a platform that only reports wins is not
honest. Each entry states what was tested, what was found, and what it does and
does not imply.

## N1: Neural xG does not beat tabular xG (diagnostic scale)

On the synthetic shot data (4,000 shots, three seeds), the neural MLP xG trained
cleanly (training loss fell from about 0.69 to 0.45 every seed) but its held-out
log loss (0.496 to 0.512) was worse than the logistic baseline's (0.480 in every
seed). The logistic model's bootstrap interval did not reach the neural values.

Interpretation: with these features the logit is close to linear, so the MLP's
extra capacity adds variance without reducing bias. This supports H1's null on this
data. It does not prove the null on real data with richer spatial context, where
non-linear interactions (defender positions, angle-distance coupling) may matter.
The full-scale evaluation is the right test and is blocked on data and compute.

What would overturn it: a real event-data campaign where the neural model, with the
spatial set encoder and matched budgets, beats the logistic baseline on held-out
proper scores with a confidence interval excluding the baseline.

## N2: A point-estimate forecast understates uncertainty

The favourite's title probability was 0.924 under point-estimate sampling and 0.881
once correlated per-season strength draws were introduced. Presenting the point
estimate alone would overstate confidence in the favourite. This is a methodological
negative result: the simpler method is misleadingly precise, so the correlated draw
is used for reported forecasts.

## Reporting discipline

Null results are not reframed as positive by changing the metric, the split, or the
effect definition after seeing the data. Any such change requires a new protocol
version and a fresh campaign, with the earlier result retained.
