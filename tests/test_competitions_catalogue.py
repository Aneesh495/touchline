"""Competition catalogue oracles: distinct entities and era notes."""

from touchline.coverage.competitions import (
    CATALOGUE,
    CompetitionKind,
    competitions_by_kind,
    is_distinct_club_world_cup_entities,
)


def test_five_leagues_present():
    leagues = {c.code for c in competitions_by_kind(CompetitionKind.LEAGUE)}
    assert leagues == {"EPL", "LALIGA", "BUNDESLIGA", "SERIEA", "LIGUE1"}


def test_five_domestic_cups_present():
    cups = {c.code for c in competitions_by_kind(CompetitionKind.DOMESTIC_CUP)}
    assert cups == {
        "FACUP",
        "COPADELREY",
        "DFBPOKAL",
        "COPPAITALIA",
        "COUPEDEFRANCE",
    }


def test_club_world_cup_entities_kept_distinct():
    assert is_distinct_club_world_cup_entities()
    assert CATALOGUE["CWC_ANNUAL"] != CATALOGUE["CWC_2025"]
    assert CATALOGUE["FIFA_INTERCONTINENTAL"].code != CATALOGUE["CWC_2025"].code


def test_ucl_notes_record_era_change():
    assert "league phase" in CATALOGUE["UCL"].notes


def test_conference_league_has_inception_note():
    assert "2021-22" in CATALOGUE["UECL"].notes
