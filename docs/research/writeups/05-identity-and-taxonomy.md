# Identity and taxonomy reconciliation across providers

## Question

How are the same real club, player, and event matched across providers that name
and encode them differently, without silently merging distinct entities?

## The problem

StatsBomb uses numeric ids; football-data.co.uk uses free-text team names ("Man
City"). Event taxonomies differ in granularity. A naive merge on a shared string
would both miss true matches (accents, suffixes) and create false ones.

## Approach

Identifiers are provider-scoped, so two ids are never equal across providers even
with the same value (`domain.identifiers`). Cross-provider links are proposed by a
resolver that normalises names (folding case, stripping accents and club suffixes)
and scores a match as exact, normalised, or fuzzy with a confidence; low-confidence
links go to a review queue rather than being applied (`ingest.identity`). The event
taxonomy is canonicalised to a small provider-agnostic set, with provider subtypes
preserved in the raw payload.

## Evidence

Tests confirm "Manchester City FC" and "Manchester City" normalise to the same key,
"Atletico Madrid" matches "Atlético Madrid", an exact match scores 1.0, and a
loose pair scores below the review threshold.

## Limitations

Fuzzy matching cannot resolve genuine ambiguity (two clubs with similar names); such
cases surface in the review queue with the evidence, for a human to decide. The
resolver proposes; it never forces.

## Conclusion

Identity resolution is auditable: every link carries its method, confidence, and the
original strings, and ambiguous links are held for review rather than applied.
