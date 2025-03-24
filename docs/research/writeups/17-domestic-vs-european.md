# Domestic versus European strength and transfer across competitions

## Question

Does a club's domestic strength transfer to European competition, and does
modelling the hierarchy of competitions improve a held-out forecast (Q2)?

## The problem

Leagues differ in strength, so a team's domestic record is not directly comparable
to its European results. A pooled model that ignores the competition hierarchy will
mis-rank cross-competition matchups.

## Approach

A cross-competition strength model links domestic leagues, cups, and European
competitions under opponent and path uncertainty, with a hierarchy so a league's
baseline strength is a level above individual teams. The transfer evaluation holds
out an entire competition and measures the held-out proper score against a pooled
baseline (`features.splits.competition_holdout_split`), with overlap controls for
players and teams appearing in several competitions.

## Status

Q2 is predeclared and exercised at small scale by the held-out-competition split
machinery; the confirmatory result on real data is open. The split integrity is
tested: a competition held out for test never appears in train.

## Conclusion

Cross-competition comparison requires the hierarchy; the transfer question is tested
by a genuine competition holdout, not by a random split that would leak the target
competition into training.
