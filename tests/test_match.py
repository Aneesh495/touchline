"""Score-state and identifier oracles."""

from touchline.domain.identifiers import Provider, TeamId
from touchline.domain.match import Appearance, ScoreState


def test_provider_scoped_ids_not_equal_across_providers():
    a = TeamId(Provider.STATSBOMB, "1")
    b = TeamId(Provider.FOOTBALL_DATA_UK, "1")
    assert a != b


def test_score_result_char():
    assert ScoreState(2, 1).result_char() == "H"
    assert ScoreState(0, 3).result_char() == "A"
    assert ScoreState(1, 1).result_char() == "D"


def test_shootout_does_not_change_regulation_result():
    # 1-1 after ET, won 4-2 on penalties: result by regulation+ET is a draw.
    s = ScoreState(
        home_regulation=1,
        away_regulation=1,
        home_shootout=4,
        away_shootout=2,
    )
    assert s.result_char() == "D"
    assert s.home_total_regulation_et == 1


def test_eligible_minutes_of_substitute():
    sub = Appearance(
        player=None,  # type: ignore[arg-type]
        team=None,  # type: ignore[arg-type]
        started=False,
        start_minute=70.0,
        end_minute=90.0,
    )
    assert sub.eligible_minutes == 20.0
