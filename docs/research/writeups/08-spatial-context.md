# Spatial context: masking, permutation invariance, and an honest ablation

## Question

How should a model consume the variable, unordered set of players visible in a 360
freeze frame, and how much does that context actually contribute?

## The problem

A freeze frame lists a variable number of players in no meaningful order, some
occluded. A model must be invariant to player order, handle a variable count with
an explicit missing mask, and never fabricate spatial features for event-only
matches.

## Approach

A Deep Sets encoder embeds each player with a shared MLP, pools by a masked mean
(invariant to order, with padded slots contributing nothing), and combines the pool
with the ball features through a head (`models.neural.set_encoder`). Off-ball
valuation is disabled on event-only matches by the feature-gated model selection in
the registry.

## Evidence

Tests confirm the prediction is identical under any permutation of the visible
players; padding does not change the result; and a context-removal ablation (an
empty player set) changes the prediction, quantifying the encoder's reliance on the
spatial context. This is the mechanism gate G07 asks for.

## Limitations

The open spatial data is a small subset of matches; the encoder's scope is declared
separately and is not conflated with event-level breadth. Whether the spatial model
beats the tabular baseline on real data is the open H1 test.

## Conclusion

The encoder is permutation invariant, mask-correct, and its contribution is
measured by an ablation rather than asserted.
