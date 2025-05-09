"""Shootout model oracles."""

from touchline.models.shootout import ShootoutModel


def test_equal_teams_are_even():
    m = ShootoutModel(conv_a=0.75, conv_b=0.75)
    p = m.win_prob_a()
    assert abs(p - 0.5) < 1e-9


def test_better_converter_favoured():
    m = ShootoutModel(conv_a=0.85, conv_b=0.65)
    assert m.win_prob_a() > 0.5


def test_probabilities_are_valid():
    m = ShootoutModel(conv_a=0.7, conv_b=0.8)
    p = m.win_prob_a()
    assert 0.0 <= p <= 1.0
    # symmetric: A's win prob vs B equals 1 - B's win prob vs A
    m2 = ShootoutModel(conv_a=0.8, conv_b=0.7)
    assert abs(p + m2.win_prob_a() - 1.0) < 1e-9
