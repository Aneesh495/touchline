# Forecast uncertainty: why a point estimate lies about confidence

## Question

Does accounting for uncertainty in team strength change a season forecast, and by
how much?

## Definitions

A forecast is the distribution over final table positions from simulating the
remaining fixtures many times. A point-estimate forecast samples each fixture from
fixed strengths. A correlated forecast draws a strength sample once per simulated
season, so a team's matches are correlated through its draw.

## Model

Dixon-Coles supplies expected goals per fixture (`models.dixon_coles`). The
simulator draws scorelines and completes the table under season rules
(`simulate.monte_carlo`), with a strength resampler for the correlated case.

## Experiment and result

On the synthetic 10-team league, the favourite's title probability was 0.924 under
point-estimate sampling and 0.881 under correlated draws, with Monte Carlo standard
errors reported per probability. The correlated draw moves mass from the favourite
to rivals because some sampled seasons give the favourite a weaker-than-expected
strength.

## Interpretation

The point estimate is misleadingly precise. The difference is not noise; it is the
structural effect of integrating over strength uncertainty rather than conditioning
on a single estimate. Reported forecasts therefore use correlated draws.

## Conclusion

Forecast uncertainty must include strength uncertainty. This is C2 in
`CONCLUSIONS.md`; it is a methodological point confirmed by construction and does
not depend on the synthetic data.
