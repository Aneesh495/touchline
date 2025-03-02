# ADR 0003: Knowledge-time feature contract

## Status
Accepted.

## Context
Leakage of future information is the most common and most damaging error in sports
modelling. It is easy to introduce and hard to spot after the fact.

## Decision
Every feature value carries a knowledge time and an availability class. The registry
allows a feature to inform a prediction only if it was knowable at or before the
prediction origin, with post-match facts barred from same-match earlier origins.

## Alternatives
- Convention and code review only: relies on vigilance and fails silently.
- A global "as-of" timestamp per row: coarser; cannot express in-match clock order.

## Consequences
Leakage becomes a checkable condition tested in three places (feature use, split,
verifier). The cost is that features must be constructed with their knowledge time,
which the feature builders handle.
