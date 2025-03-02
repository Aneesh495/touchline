# ADR 0004: Non-uniform match clock

## Status
Accepted.

## Context
Football time is piecewise: periods restart the minute counter, lengths differ,
stoppage time extends a period, and a shootout is not on the match clock at all. A
single 0..90+ axis loses the distinctions that score-state features depend on.

## Decision
Represent time as (period, second-in-period, added-second). Ordering sorts across
periods without pretending they share a clock; a derived monotone axis exists only
for plotting.

## Alternatives
- A single elapsed-seconds integer: simple but conflates 45+2 with 47 and mixes
  shootouts into regulation.

## Consequences
Extra time and shootouts never contaminate regulation counts. The cost is a richer
clock type that all time comparisons go through, which is desirable.
