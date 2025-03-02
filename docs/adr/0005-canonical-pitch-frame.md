# ADR 0005: Canonical attacking pitch frame

## Status
Accepted.

## Context
Providers use different pitch frames and attacking directions flip at half time. A
model wanting "distance to goal" must know the frame and direction, and a flipped
pitch is a classic silent bug.

## Decision
Canonicalise all locations to a frame where x grows toward the attacking goal and y
to the attacking team's right. Transforms are explicit and reversible; the semantic
verifier checks that shots cluster in the attacking half.

## Alternatives
- Keep provider frames and branch in models: spreads direction logic everywhere.

## Consequences
Models consume one frame and never branch on provider. A flipped pitch is caught by
the verifier. The cost is a transform step in each parser.
