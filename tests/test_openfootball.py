"""openfootball parser oracles."""

from touchline.parse.openfootball import parse_openfootball

SAMPLE = """
Matchday 1

[Fri Aug/12]
Crystal Palace  0-2  Arsenal
Fulham          2-2  Liverpool

[Sat Aug/13]
Bournemouth     2-0  Aston Villa
Leeds United    2-1  Wolverhampton Wanderers

some stray commentary line that is not a match
"""


def test_parses_matches_and_skips_noise():
    matches, skipped = parse_openfootball(SAMPLE)
    assert len(matches) == 4
    assert skipped >= 1  # the stray commentary line


def test_results_and_scores():
    matches, _ = parse_openfootball(SAMPLE)
    palace = matches[0]
    assert palace.home_team == "Crystal Palace"
    assert palace.away_team == "Arsenal"
    assert palace.home_goals == 0 and palace.away_goals == 2
    assert palace.result == "A"
    fulham = matches[1]
    assert fulham.result == "D"


def test_date_header_attached():
    matches, _ = parse_openfootball(SAMPLE)
    assert matches[0].date_text == "Fri Aug/12"
    assert matches[2].date_text == "Sat Aug/13"


def test_colon_separator_also_parsed():
    matches, _ = parse_openfootball("Team A 3:1 Team B\n")
    assert len(matches) == 1
    assert matches[0].home_goals == 3 and matches[0].away_goals == 1
