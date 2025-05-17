"""Contract-horizon survival oracles."""

from touchline.economics.contract_horizon import (
    Outcome,
    SurvivalRecord,
    kaplan_meier,
    median_survival,
)


def test_survival_decreases_with_transfers():
    records = [
        SurvivalRecord("a", 6, Outcome.TRANSFER, horizon_months_at_start=12),
        SurvivalRecord("b", 12, Outcome.TRANSFER, horizon_months_at_start=12),
        SurvivalRecord("c", 18, Outcome.CENSORED, horizon_months_at_start=12),
        SurvivalRecord("d", 24, Outcome.EXTENSION, horizon_months_at_start=12),
    ]
    curve = kaplan_meier(records, horizon_band=(0, 18))
    survivals = [s for _, s in curve]
    # survival is non-increasing
    assert all(a >= b for a, b in zip(survivals, survivals[1:], strict=False))
    assert survivals[-1] < 1.0


def test_horizon_band_filters_cohort():
    records = [
        SurvivalRecord("a", 6, Outcome.TRANSFER, horizon_months_at_start=6),
        SurvivalRecord("b", 6, Outcome.TRANSFER, horizon_months_at_start=36),
    ]
    short = kaplan_meier(records, horizon_band=(0, 12))
    # only the short-horizon player is in the cohort; one transfer drops survival
    assert short[-1][1] < 1.0


def test_censored_and_extension_do_not_count_as_transfer():
    records = [
        SurvivalRecord("a", 6, Outcome.CENSORED, horizon_months_at_start=12),
        SurvivalRecord("b", 12, Outcome.EXTENSION, horizon_months_at_start=12),
    ]
    curve = kaplan_meier(records, horizon_band=(0, 24))
    # no transfers -> survival stays at 1.0
    assert all(s == 1.0 for _, s in curve)
    assert median_survival(curve) is None
