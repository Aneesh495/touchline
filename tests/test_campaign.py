"""Experiment campaign oracles. Neural runs skipped cleanly without torch."""

from touchline.experiments.campaign import (
    run_strength_uncertainty,
    run_xg_comparison,
)


def test_xg_comparison_runs_three_seeds():
    recs = run_xg_comparison(seeds=(0, 1, 2), epochs=100)
    logistic = [r for r in recs if r.model == "logistic"]
    assert len(logistic) == 3
    # every logistic run reports a finite log loss
    for r in logistic:
        assert r.metrics["log_loss"] > 0
        assert r.metrics["ll_ci_lo"] <= r.metrics["log_loss"] <= r.metrics["ll_ci_hi"]


def test_xg_comparison_records_neural_status():
    recs = run_xg_comparison(seeds=(0,), epochs=50)
    neural = [r for r in recs if r.model == "neural"]
    assert len(neural) == 1
    # either it completed (torch present) or it is recorded as blocked
    assert neural[0].status in ("completed", "blocked")
    if neural[0].status == "completed":
        # learning: training loss fell
        assert neural[0].metrics["loss_end"] < neural[0].metrics["loss_start"]


def test_strength_uncertainty_widens_distribution():
    recs = run_strength_uncertainty(n_sims=1500)
    point = next(r for r in recs if r.model == "point_estimate")
    corr = next(r for r in recs if r.model == "correlated_draws")
    # Correlated draws should not increase the favourite's title probability.
    assert (
        corr.metrics["title_prob_favourite"]
        <= point.metrics["title_prob_favourite"] + 0.02
    )
