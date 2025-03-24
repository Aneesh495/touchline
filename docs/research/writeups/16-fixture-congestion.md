# Fixture congestion: rest, travel, and honest proxies

## Question

Is a congested schedule associated with reduced performance, and how confident can
we be in a travel proxy?

## Approach

Rest days between matches come straight from the known schedule, so they are exact.
Travel distance, by contrast, is a proxy: without venue coordinates and travel
logs it is estimated, and that uncertainty is declared rather than hidden. The
association model uses rest days and a flagged travel proxy as features for
subsequent performance (points, action value), with knowledge time respected so
only past schedule information informs a prediction.

## Confounders

Congestion correlates with success (teams in more competitions play more and are
usually stronger), so a raw congestion effect confounds with strength. The model
conditions on team strength and states the residual confounding as a limitation.

## Status

Hypothesis H8. The schedule features and the knowledge-time handling are
implemented; the confirmatory estimate awaits the full schedule data.

## Conclusion

Rest is exact; travel is a declared proxy. Any congestion association is reported
conditional on strength, with the confounding named, not as a causal fatigue effect.
