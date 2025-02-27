# Possession action value: crediting what moves the ball toward a goal

## Question

How should an on-ball action be valued so that advancing the ball into a dangerous
area is credited and losing it there is penalised, without claiming a causal effect?

## Related work

Decroos et al. (KDD 2019) value actions by their effect on scoring and conceding
probability over a short horizon. Expected threat (Karun Singh) values pitch
location directly via a Markov chain over cells.

## Definitions

For the game state after an action we estimate P(score within horizon) and
P(concede within horizon). The state value is their difference. An action's value
is V(after) - V(before), with the before-state value negated across a turnover so
value is always from the perspective of the team ending in control.

## Model

Two logistic state models trained on causal labels built by looking only forward up
to the horizon (`models.action_value`). Expected threat is solved by value
iteration over a grid with absorbing goal and turnover states
(`models.expected_threat`); the move operator is sub-stochastic so the solve
converges.

## Experiment and result

On synthetic sequences that advance toward goal and score more often when they
reach further, the action-value model learns that advanced states precede goals:
the state value near the goal exceeds the midfield value, and training loss falls.
The expected-threat grid values cells near the opponent goal above cells near the
team's own goal, and all values lie in [0, 1] as probabilities must.

## Limitations

These are predictive values, not causal attributions. A player credited with high
action value may be benefiting from teammates and opponents; the writeup on
role-adjusted contribution addresses this and states it as a limitation rather than
resolving it.

## Conclusion

The before/after formulation with a turnover-aware perspective gives a coherent,
converging action value that behaves as expected spatially. It is a predictive
instrument and is labelled as such wherever it informs a comparison.
