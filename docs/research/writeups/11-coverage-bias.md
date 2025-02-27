# Coverage bias: event depth is not uniform

## Question

What bias is introduced by the fact that event and tracking data cover only a small,
non-random subset of matches, and how does the system keep this visible?

## The problem

Match results are broad; event data is narrower; 360/tracking data is rarest and
concentrated in specific competitions and seasons. A model trained on the event
subset and applied broadly would carry the subset's selection bias, and a UI that
implied uniform depth would mislead.

## Approach

A coverage matrix records, per competition-season, the unique counts at each depth
(results, events, tracking) from identity sets, so a duplicated feed does not
inflate a count (`coverage.matrix`). The field level is an enum the interface uses
to show genuine differences in depth rather than a single coverage number. A profile
check reports each shortfall against a required minimum.

## Evidence

Tests confirm the matrix distinguishes results-only, event, and tracking cells;
unique counting prevents a repeated match id from inflating the total; and the
profile check reports both a match shortfall and a missing competition.

## Conclusion

Coverage is reported honestly at three depths with unique counts. The interface can
show that an event-level claim rests on fewer matches than a results-level one,
which is the first requirement of gate G01.
