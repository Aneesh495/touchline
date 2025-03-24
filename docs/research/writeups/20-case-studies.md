# Case studies: a predeclared rule and a narrative that fails

## Selection rule

Case studies are chosen by a predeclared rule to avoid cherry-picking: take the
club with the largest gap between its final league position and its expected
position under the fitted score model (the biggest over- or under-performer), and
the player with the largest gap between goals and expected goals over a minimum
exposure. At least one case is chosen specifically because a popular narrative does
not match the data.

## A narrative that fails (illustrative structure)

A common narrative is that a team "deserved" a higher finish because it dominated
possession. The data path to test this: compute the team's expected points from the
fitted score model and compare to its actual points. If actual exceeds expected, the
team over-performed its underlying play and the "deserved better" narrative is the
reverse of the truth. The structure is implemented through the expected-points
measure (`docs/STATISTICAL_DICTIONARY.md`) and the simulator's expected-position
output; the specific club named is filled from the full-data run.

## Why this matters

A case study chosen after seeing which story is nice is not evidence. A predeclared
rule, applied to frozen artifacts, is. The deliberate inclusion of a failing
narrative guards against the platform only telling flattering stories.

## Status

The selection rule and the measures it needs (expected points, expected position,
goals minus xG with exposure) are implemented. The named cases come from the full
real-data run and are reported with the same uncertainty as any other result.

## Conclusion

Case studies follow a predeclared rule on frozen artifacts and include a case where
the data contradicts the popular story, so they inform rather than flatter.
