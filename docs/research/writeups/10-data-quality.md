# Data quality: reporting discrepancies instead of forcing agreement

## Question

What should a pipeline do when the goal events do not add up to the recorded score,
or a red card has no matching manpower change?

## Principle

Report, do not repair. Altering source data to force agreement destroys the signal
that something is wrong. The right output is a discrepancy report with the numbers
involved, leaving the decision to a human.

## Approach

Reconciliation checks compare goal events plus own goals against the recorded score,
check that each side has eleven starters, and check that red cards match manpower
reductions (`quality.reconcile`). Known acceptable reasons for a mismatch (own
goals, extra time, shootouts, provider assist policy) are handled explicitly so a
genuine problem is distinguished from an expected accounting difference.

## Evidence

Tests confirm a clean score reconciles, an own goal is accounted for, a real score
mismatch is reported rather than fixed, a ten-player lineup is flagged, and a red
card without a manpower change is flagged.

## Conclusion

Discrepancies are surfaced with evidence and the source is left untouched. This is
how aggregates can disagree within permitted bounds without the pipeline silently
inventing agreement.
