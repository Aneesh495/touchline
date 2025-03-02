# ADR 0009: Dixon-Coles over plain independent Poisson

## Status
Accepted.

## Context
Modelling home and away goals as independent Poisson is simple but overstates the
probability of draws and 1-0/0-1 scores, which matters for both evaluation and
forecasting.

## Decision
Use the Dixon-Coles low-score dependence correction on the four lowest scorelines,
with identifiable (sum-zero) attack and defence parameters, a baseline log-rate, and
a home-scoring boost, fit by maximum likelihood.

## Alternatives
- Independent Poisson: biased on low scores.
- A full bivariate Poisson or copula: more parameters than the data here supports.

## Consequences
Scoreline and result probabilities are more realistic for close games. The cost is a
non-linear fit (L-BFGS) and the rho parameter, both handled in the model.
