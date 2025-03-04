# Walkthrough: a distribution becomes a table forecast

This traces how fitted team strengths become a distribution over final positions.

1. **Fit strength.** `models.dixon_coles.DixonColesModel.fit`
   (`models/dixon_coles.py`) estimates attack, defence, baseline, home boost, and
   the low-score rho by maximum likelihood, giving `expected_goals(home, away)` for
   any fixture.

2. **Sample a season.** `simulate.monte_carlo.SeasonSimulator.simulate`
   (`simulate/monte_carlo.py`) draws one strength sample per simulated season (the
   `strength_resampler`), then samples each remaining fixture's scoreline from the
   model, so a team's matches are correlated through its draw.

3. **Build the table.** `simulate.rules.compute_table` (`simulate/rules.py`) applies
   the season's points and ordered tie-breaks (including head-to-head) and any
   deductions, then ranks.

4. **Aggregate.** Over many draws, `SimulationResult` records each team's finishing
   position counts, giving title, top-n, and expected-position probabilities with a
   Monte Carlo standard error. `simulate.enumerate_small` provides an exact check
   for tiny tournaments.

Diagram: `docs/diagrams/svg/09-season-rule-execution.svg`.
