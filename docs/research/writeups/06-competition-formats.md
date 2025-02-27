# Competition formats: not hardcoding one season's rules

## Question

How can a simulator reproduce league tables and Champions League brackets across
eras whose rules differ, without hardcoding one season's conventions?

## The problem

Points-for-a-win changed historically. Tie-break orders differ by league (goal
difference first in England, head-to-head first in Spain). The Champions League ran
a group stage for decades, abolished the away-goals rule from 2021-22, and switched
to a 36-team league phase in 2024-25. A single hardcoded ruleset would be wrong for
most seasons.

## Approach

League rules are an explicit object: points per result, an ordered tie-break list,
and deductions (`simulate.rules`). The table builder applies exactly the rules it
is given, including head-to-head tie-breaks computed from the fixtures. The UCL
module selects behaviour by season: group stage versus league phase, away goals
only through 2020-21, two-legged aggregate with extra time and penalties, and the
league-phase position-to-round mapping (`simulate.ucl`).

## Evidence

Tests confirm: three-points and two-points configurations both work; a head-to-head
tie-break orders two level teams correctly; a point deduction drops a team below a
rival; away goals decide a level tie in 2019 but not in 2022 (which goes to extra
time then penalties); and the league-phase mapping sends positions 1-8 direct,
9-24 to a play-off, and 25+ out.

## Conclusion

Era-specific rules are modelled as data, not code branches scattered through the
engine, so the right rules apply to the right season by construction. This supports
gate G09's requirement that old and current UCL formats both reproduce.
