# ADR 0011: Era-specific rules as data, not code branches

## Status
Accepted.

## Context
Competition rules change over time (points per win, tie-break order, away goals, UCL
format). Scattering season checks through the engine makes it error-prone and hard
to audit.

## Decision
Represent league rules as an explicit object (points, ordered tie-breaks,
deductions) that the table builder applies verbatim. Represent UCL era behaviour as
small selector functions keyed by season.

## Alternatives
- Hardcode one season's rules: wrong for most seasons.
- A rules DSL: more than this project needs.

## Consequences
The right rules apply to the right season by construction, and a new season's rules
are a new object, not a code change in the engine. The cost is that callers must
supply the correct rules object, which the season metadata drives.
