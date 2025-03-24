# Penalties and goalkeeping: small samples, repeated participants, retakes

## Question

How should penalty conversion and goalkeeper effects be estimated when takers and
keepers appear repeatedly, samples are small, and retakes complicate the count?

## The counting problem

A retaken penalty is one scoring opportunity, not two; counting both inflates the
denominator and distorts conversion. Shootout kicks are a different process from
regulation penalties and must be separated. Both rules are encoded in the domain:
a `Shot` carries `is_penalty` and `is_shootout`, and `counts_toward_regulation` is
False for shootout kicks (`domain.events`), so regulation penalty conversion never
mixes in shootout kicks.

## Model

Penalty conversion is a hierarchical rate per taker and per keeper, shrunk toward
the population rate by exposure (`models.hierarchical`), because most takers have
few penalties. Reporting the shrunk rate with its exposure prevents a two-from-two
taker from topping a confident leaderboard.

## Goalkeeping

Goals prevented is only meaningful with a post-shot model that uses shot placement,
which requires observed placement inputs. Where those inputs do not exist, the
project does not fabricate them from the final score; the measure is simply not
computed, and that limitation is stated in the dictionary.

## Evidence

The domain tests confirm a shootout penalty does not count toward regulation and a
regulation penalty does. The shrinkage tests confirm small-sample takers are pulled
toward the mean.

## Conclusion

Penalty and goalkeeper estimates use partial pooling, exclude shootouts from
regulation counts, count retakes once, and report uncertainty. Goals prevented is
computed only where placement inputs genuinely exist.
