"""Deterministic integration test for the end-to-end demo pipeline."""

import io

from touchline.pipeline.demo import run_demo


def test_demo_runs_end_to_end_and_is_sensible():
    buf = io.StringIO()
    report = run_demo(out=buf, n_sims=1000)
    text = buf.getvalue()
    assert "Expected goals" in text
    assert "Simulated season" in text
    # The trained xG model must beat the base-rate predictor on held-out log loss.
    assert report["xg_log_loss"] < report["xg_log_loss_base"]
    # A close central shot should have a substantial xG.
    assert 0.3 < report["xg_example"] < 0.99
    # Home advantage is positive in the fitted score model.
    assert report["dc_home_adv"] > 0
    # Title probability is a valid probability.
    assert 0.0 <= report["title_prob"] <= 1.0
    # The strongest-attack team is the title favourite in this synthetic world.
    assert report["title_favourite"] == report["strongest_team"]
    # Strong team at home beats weak team more often than not.
    assert report["h2h_strong_home_win"] > 0.5
