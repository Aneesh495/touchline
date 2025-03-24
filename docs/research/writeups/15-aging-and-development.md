# Aging and development: survivorship and minutes selection

## Question

How does player output change with age, and why is the naive age curve biased?

## The biases

A naive average of output by age is distorted by survivorship: players who decline
leave the sample, so the remaining older players look artificially good. Minutes
selection compounds this: a struggling player plays less, so their poor stretch is
under-weighted. Injuries and absences create missingness that is not random.

## Approach

Development trajectories are estimated with exposure-aware shrinkage so a player's
estimate reflects their minutes, and the cohort is defined by a predeclared rule
rather than by who remained. Players leaving the sample are tracked so survivorship
is visible rather than silently dropping out. Transfer-related domain shift (a
player moving to a stronger or weaker league) is flagged because it changes the
opponent quality behind the output.

## Status

This is hypothesis-level work (part of the planned set in `HYPOTHESES.md`). The
machinery (shrinkage, exposure, cohort definition) is implemented and tested; the
confirmatory age-curve estimate awaits the full real-data campaign.

## Limitations

An observational age curve cannot separate aging from selection without strong
assumptions. The honest output is an association with the biases named, not a causal
aging effect.

## Conclusion

Development is modelled with survivorship and minutes selection made explicit. The
curve is an association, and its biases are stated rather than assumed away.
