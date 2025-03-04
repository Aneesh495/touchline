# Walkthrough: an event changes action value

This traces how an action's value is computed from a sequence of events.

1. **Segment.** `features.possession.segment_possessions`
   (`features/possession.py`) partitions the ordered events into possessions,
   switching on a controlled action by a different team, not on a contested duel,
   and flagging goalkeeper control and period boundaries.

2. **State features.** `models.action_value.ActionValueModel.state_features`
   (`models/action_value.py`) builds the state after each event from its canonical
   location, a distance-to-goal term, event-type flags, and the period.

3. **Causal labels.** `build_labels` looks forward at most `horizon` events: if the
   acting team scores first the score label is 1, if the opponent scores first the
   concede label is 1. No future beyond the horizon and no label from the past
   leaks in.

4. **Value.** `action_values` computes `V(after) - V(before)` for each action,
   where `V = P(score) - P(concede)` from the two fitted logistic models, and the
   before-state value is negated on a turnover so winning the ball in a dangerous
   area is credited to the team that gains it.

Diagram: `docs/diagrams/svg/06-action-value-target.svg`.
