# Statistical dictionary

Every measure Touchline computes is defined here with its entity grain, eligible
competitions, unit, numerator, denominator, exclusions, and known bias. The
machine-readable version lives at `docs/statistical_dictionary.json` and is loaded
by `touchline.dictionary` so code and prose cannot drift. Providers do not always
mean the same thing by a term; where a definition is provider-specific it says so.

A measure is only computed where its denominator is real and meaningful. A ten
minute substitute is not ranked above an established player without shrinkage and
exposure disclosure (see `models.hierarchical`).

## Results and opportunity

| Measure | Grain | Numerator | Denominator | Exclusions / notes |
|---------|-------|-----------|-------------|--------------------|
| points | team-season | sum of result points | matches played | points-per-win is season-specific |
| points per match | team-season | points | matches played | low-sample early season noisy |
| goal difference | team-season | goals for minus against | — | includes extra time where applicable |
| expected points | team-season | sum of modelled win/draw mass | matches | under the declared score model |

## Shooting and finishing

| Measure | Grain | Numerator | Denominator | Exclusions / notes |
|---------|-------|-----------|-------------|--------------------|
| goals | player/team | goals scored | — | own goals excluded from the scorer |
| non-penalty goals | player | goals minus penalties | — | regulation penalties only |
| xG | shot | modelled goal probability | — | shootout kicks excluded |
| non-penalty xG | shot | xG on non-penalty shots | — | separates penalty mean |
| xG per shot | player | sum xG | shots | denominator must be real shots |
| conversion | player | goals | shots | small samples shrunk |

## Passing and creation

| Measure | Grain | Numerator | Denominator | Exclusions / notes |
|---------|-------|-----------|-------------|--------------------|
| pass accuracy | player | completed passes | attempted passes | provider completion policy |
| progressive passes | player | passes advancing toward goal by a threshold | — | threshold stated with the measure |
| key passes | player | passes leading to a shot | — | provider definition |

## Possession and tactics

| Measure | Grain | Numerator | Denominator | Exclusions / notes |
|---------|-------|-----------|-------------|--------------------|
| possession share | team-match | own controlled time | total controlled time | provider definition |
| action value | action | change in score minus concede probability | — | over a declared horizon |
| expected threat | pitch cell | probability of scoring before loss | — | from a converged grid solve |

## Discipline

| Measure | Grain | Numerator | Denominator | Exclusions / notes |
|---------|-------|-----------|-------------|--------------------|
| yellow cards | player/team | yellows shown | — | second yellow handling is league-specific |
| red cards | player/team | straight reds plus second yellows | — | reconciled against manpower events |

## Set pieces and penalties

| Measure | Grain | Numerator | Denominator | Exclusions / notes |
|---------|-------|-----------|-------------|--------------------|
| corner conversion | team | goals within a corner-possession horizon | corners | horizon stated; rare-event shrinkage |
| penalty conversion | taker | penalties scored | penalties taken | shootout kicks excluded; retakes count once |

Every per-90, per-opportunity, per-possession, opponent-adjusted, role-adjusted,
and competition-adjusted variant is computed only where its denominator is real.
Unresolved discrepancies between individual and team aggregates are reported, not
forced into agreement (see `quality.reconcile`).
