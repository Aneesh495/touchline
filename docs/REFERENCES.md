# References and attribution

This project builds on established ideas in football analytics. These references
attribute the ideas and datasets used; Touchline implements its own versions and
does not claim to reproduce any published result.

## Ideas

- Decroos, Bransen, Van Haaren, Davis. "Actions Speak Louder than Goals:
  Valuing Player Actions in Soccer." KDD 2019.
  https://tomdecroos.github.io/reports/kdd19_tomd.pdf
  Basis for the action-value idea: value an action by its effect on the scoring
  and conceding probability over a short horizon. Touchline's
  `models.action_value` is an original implementation of this concept.

- Dixon, Coles. "Modelling Association Football Scores and Inefficiencies in the
  Football Betting Market." Applied Statistics, 1997.
  Basis for the low-score dependence correction in `models.dixon_coles`.

- Expected threat (grid Markov chain over pitch cells), popularised by Karun Singh.
  Basis for `models.expected_threat`, implemented here with explicit absorbing
  goal and turnover states and a converged value iteration.

- Expected goals is a widely used shot-quality concept; the geometric features
  (distance and the angle subtended by the goal) are standard. `models.xg_logistic`
  and `models.neural.spatial_xg` are original implementations.

- Deep Sets (Zaheer et al., 2017) for permutation-invariant set functions. Basis
  for the masked player encoder in `models.neural.set_encoder`.

## Datasets

- StatsBomb / Hudl open data. https://github.com/hudl/open-data
  Used under the StatsBomb open-data user agreement; attribution required.

- football-data.co.uk historical results. https://www.football-data.co.uk/data.php

- football-data.org coverage (reference). https://www.football-data.org/coverage

- UEFA competition regulations (for the rules engine).
  https://documents.uefa.com/

## Scope of attribution

Touchline reimplements these ideas against its own typed domain and evaluates them
on its own data pipeline. Reported numbers are from Touchline's models, not from
the cited works. Where a finding is null (see `docs/research/NEGATIVE_RESULTS.md`),
that is Touchline's own result on its own data, not a comment on the cited work.
