"""Property-based tests for domain invariants, using Hypothesis.

These assert properties that must hold for all valid inputs, not just hand-picked
examples: clock ordering is a total order, canonical geometry stays in range,
result probabilities sum to one, and the coordinate transform round-trips.
"""

from hypothesis import given
from hypothesis import strategies as st

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.geometry import AttackDirection, Pitch, Point
from touchline.models.elo import EloModel

periods = st.sampled_from(
    [p for p in PeriodKind if p is not PeriodKind.SHOOTOUT]
)


@given(
    p1=periods,
    s1=st.integers(min_value=0, max_value=45 * 60),
    p2=periods,
    s2=st.integers(min_value=0, max_value=45 * 60),
)
def test_clock_ordering_is_consistent(p1, s1, p2, s2):
    a = MatchClock(p1, s1)
    b = MatchClock(p2, s2)
    # Exactly one of <, ==, > holds (trichotomy).
    lt = a < b
    gt = b < a
    eq = a == b
    assert (lt + gt + eq) == 1


@given(
    x=st.floats(min_value=0, max_value=120, allow_nan=False),
    y=st.floats(min_value=0, max_value=80, allow_nan=False),
    d=st.sampled_from(list(AttackDirection)),
)
def test_canonical_point_in_range(x, y, d):
    sb = Pitch(120, 80, y_down=True)
    p = sb.to_canonical(x, y, d)
    assert 0.0 <= p.x <= 1.0
    assert 0.0 <= p.y <= 1.0


@given(
    x=st.floats(min_value=0.0, max_value=1.0),
    y=st.floats(min_value=0.0, max_value=1.0),
)
def test_distance_and_angle_finite(x, y):
    p = Point(x, y)
    dist = p.distance_to_goal_m()
    angle = p.shot_angle_rad()
    assert dist >= 0.0
    assert 0.0 <= angle <= 3.1416


@given(
    rh=st.floats(min_value=1000, max_value=2200),
    ra=st.floats(min_value=1000, max_value=2200),
)
def test_elo_probs_sum_to_one_for_all_ratings(rh, ra):
    elo = EloModel()
    elo.ratings = {"h": rh, "a": ra}
    ph, pd, pa = elo.predict_result_probs("h", "a")
    assert abs(ph + pd + pa - 1.0) < 1e-9
    assert 0.0 <= ph <= 1.0 and 0.0 <= pd <= 1.0 and 0.0 <= pa <= 1.0
