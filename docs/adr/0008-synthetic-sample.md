# ADR 0008: Synthetic sample data, labelled, for the demo

## Status
Accepted.

## Context
The demo and tests must run offline and deterministically, but real provider data
has licensing and size constraints and is not appropriate to commit.

## Decision
Generate a small synthetic sample from a fixed seed with a known data-generating
process. It is clearly labelled synthetic, is never counted toward a real-data
coverage gate, and doubles as a known-truth regression fixture.

## Alternatives
- Commit a slice of real provider data: licensing risk and redistribution concerns.
- No bundled data: the demo would need a network pull to show anything.

## Consequences
A fresh reader can run the demo with no download. Because the truth is known, the
demo also checks that fitted models recover the planted structure. The cost is that
demo numbers are synthetic and are labelled as such everywhere.
