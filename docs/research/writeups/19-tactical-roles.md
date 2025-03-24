# Tactical roles: learning role from actions, not from a label

## Question

Can a player's role be characterised from the actions and positions they actually
produce, rather than from a provider's position label, and does role context change
how a contribution should be read?

## Approach

A role representation is learned from the distribution of a player's action types
and canonical locations. Because actions carry a canonical attacking frame
(`domain.geometry`), a left-sided and right-sided player are distinguished by their
y-distribution rather than conflated, and the attacking-direction convention keeps
the representation stable across halves. Role context then adjusts contribution:
the same raw output means different things for a holding midfielder and a forward.

## Why not the position label

Provider position labels are coarse and sometimes stale (a player nominally a
winger may play as a wing-back). Learning the role from actions captures what a
player did, which is what a role-adjusted contribution needs.

## Status

The geometry and action-type features that a role representation builds on are
implemented and tested; a held-out role analysis is part of the planned campaign.

## Limitations

Role is a description of behaviour, not a cause of output. A role-adjusted
contribution reduces but does not remove teammate and opponent confounding, which
is stated wherever such a contribution is reported.

## Conclusion

Role is learned from actions in a direction-stable canonical frame, and contribution
is read in the light of role, with the confounding limitations stated.
