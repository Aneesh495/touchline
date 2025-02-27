# Role-adjusted contribution needs shrinkage and exposure

## Question

Why should raw per-90 leaderboards not be trusted, and how does partial pooling fix
the small-sample problem?

## The problem

A player with two goals in ninety minutes has a raw rate of 2.0 per 90, far above a
striker with twenty in three thousand minutes (0.6 per 90). Ranking by raw rate
promotes the cameo above the established player, which is absurd.

## Approach

An empirical-Bayes shrinkage pulls each rate toward the population mean by a weight
that grows with exposure (`models.hierarchical`). Small samples are pulled strongly
to the prior; large samples keep their own rate. Exposure accompanies every
estimate so a ranking discloses the sample behind it.

## Evidence

Tests confirm the cameo's raw rate exceeds the established player's but its
shrinkage weight is far smaller, so after shrinkage the established player ranks
higher; and with heavy exposure the shrunk rate stays within 0.1 of the raw rate.

## Limitations

Shrinkage handles sampling noise, not confounding. A player's output still mixes
their own skill with teammate and opponent quality. Role and context adjustment
reduce but do not remove this; the residual is reported as a limitation, never as a
causal individual effect.

## Conclusion

Rankings use shrunk, exposure-disclosed estimates. A ten-minute substitute is never
ranked above an established player on raw rate alone.
