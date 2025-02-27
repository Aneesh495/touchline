# Set pieces and rare events: partial pooling over confident leaderboards

## Question

How should corner and free-kick conversion be estimated when goals from them are
rare, so a handful of goals does not produce a confident but meaningless
leaderboard?

## The problem

A team might score from three of forty corners one season. The raw 7.5% rate has
enormous sampling uncertainty, yet a naive table would rank teams by it as if it
were precise. Rare-event rates demand partial pooling and honest intervals.

## Approach

Conversion is defined with an explicit denominator and a declared possession or time
horizon (see the statistical dictionary). Estimates use the hierarchical shrinkage
model so a team with few corners is pulled toward the league rate, and the between-
team variance is reported rather than a point leaderboard. Shootout kicks are
excluded and retaken penalties count once.

## Evidence

The shrinkage model's tests confirm small samples shrink more than large ones, which
is exactly the behaviour rare-event conversion needs. The dictionary records the
corner and penalty definitions with their denominators and exclusions.

## Limitations

Even with pooling, a single season of corners carries wide intervals; the honest
output is a distribution, not a ranking. Repeatability (H5) is predeclared and will
be reported with its interval whether positive or null.

## Conclusion

Rare-event conversion is reported with partial pooling and uncertainty. No confident
leaderboard is built from a handful of goals.
