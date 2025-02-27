# Chronology and leakage: making a timing bug a type error

## Question

How can a football modelling pipeline prevent future information from leaking into
earlier predictions, so reported performance is honest?

## The problem

Football data is full of tempting leaks: a season's final table position, a late
substitution, a goal later in the match. Using any of them to predict an earlier
moment inflates performance and would not generalise to live use.

## Approach

Every feature carries a knowledge time (a date and, for in-match features, a match
clock) and an availability class (pre-match, in-match, post-match). The registry's
precedence rule allows a feature to inform a prediction origin only if it was
knowable at or before that origin, with post-match facts explicitly barred from
informing same-match in-match or pre-match origins (`features.registry`).

Splits add the second half: a competition-season is a group, and no group straddles
the train/test boundary, so duplicated feeds and within-group correlation cannot
leak across the split (`features.splits`).

## Evidence

The feature tests confirm a post-match final-position feature cannot inform an
in-match origin on the same date, an in-match score difference known at minute 80
cannot inform a minute-10 prediction, and a prior-date pre-match rating is usable.
The split tests confirm a mid-season cut is flagged as violating group integrity
while a season-boundary cut is clean. The verifier recomputes the leakage check
from raw records and rejects a bundle whose feature became known after its origin.

## Conclusion

Leakage is caught in three independent places: at feature-use time, at split time,
and at verification time. This is C3 in `CONCLUSIONS.md`.
