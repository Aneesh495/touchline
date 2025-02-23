# Methods

This document derives the models Touchline uses and states the evaluation
protocol. It is written so a reader can reproduce the reasoning from the source in
`src/touchline/models`.

## Expected goals (logistic)

A shot's goal probability is modelled as

    P(goal | x) = sigmoid(w . x + b)

with features x = (distance, angle, header, penalty, free kick, corner, counter).
The angle is the angle subtended by the goal mouth from the shot location, which
captures how much open goal is available; distance and angle together are the
classic xG geometry. Fitting minimises the mean weighted binary cross-entropy by
gradient descent (`models.xg_logistic`), with weights available to counter the
heavy class imbalance of shots. Feature standardisation uses training statistics
only, so a validation or test shot is transformed with training-time means and
scales and no information leaks through scaling.

## Expected goals (neural)

The neural variant (`models.neural.spatial_xg`) replaces the linear term with a
small MLP on the same features, trained from random initialisation with Adam. It
exists to test H1: whether a non-linear model beats the linear one on matched
inputs. The comparison uses identical features, splits, and proper scores.

## Expected threat

Expected threat assigns a value V(z) to each pitch cell z:

    V(z) = s(z) g(z) + (1 - s(z)) sum_z' m(z, z') V(z')

where s(z) is the probability of shooting from z, g(z) the chance such a shot
scores, and m(z, z') the probability of a successful move from z to z'. Losing the
ball is an absorbing zero-value state, reached implicitly because the move
probabilities from a cell sum to less than one (the deficit is the turnover rate).
The operator is a sub-stochastic contraction, so value iteration converges
(`models.expected_threat`).

## Action value

Following Decroos et al. (KDD 2019), each action is valued by its change in the
controlling team's probability of scoring and of conceding within a declared
horizon of actions. Two logistic models estimate the score and concede
probabilities of the state after an action from causal labels. The action value is
V(after) - V(before), where the before-state value is negated on a turnover so the
value is always from the perspective of the team that ends in control
(`models.action_value`).

## Team strength

Two baselines. Elo (`models.elo`) is an online rating with a home-advantage offset
and a margin-scaled update, split into win/draw/loss via a gap-dependent draw
share. Dixon-Coles (`models.dixon_coles`) models home and away goals as Poisson
with team attack and defence parameters, a baseline log-rate, a home-scoring boost,
and the low-score dependence correction, fit by maximum likelihood with a sum-zero
identifiability constraint.

## Hierarchical effects

Per-entity rates are shrunk toward the population mean by an empirical-Bayes weight
that depends on exposure (`models.hierarchical`). Small samples are pulled strongly
toward the prior; large samples are trusted. Exposure accompanies every estimate so
a ranking discloses the sample behind it.

## Evaluation protocol

Splits are chronological with group integrity: a competition-season never straddles
the train/test boundary (`features.splits`). Transfer uses a held-out competition.
Calibration is fit on validation only and reported with reliability tables and ECE
(`models.calibration`). Uncertainty is bootstrapped at the correct unit (shots for
xG, matches for score models, competition-seasons for forecasts). Decisive neural
comparisons use at least three seeds with matched budgets and validation-based early
stopping.
