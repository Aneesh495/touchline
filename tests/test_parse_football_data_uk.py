"""football-data.co.uk CSV parser oracles."""

from touchline.parse.football_data_uk import parse_football_data_uk_csv

CSV = """Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HTHG,HTAG,HS,AS,HST,AST,HC,AC,HF,AF,HY,AY,HR,AR,Referee
E0,12/08/2022,Crystal Palace,Arsenal,0,2,A,0,1,10,12,3,5,4,6,11,9,2,1,0,0,A Taylor
SP1,13/08/2022,Osasuna,Sevilla,2,1,H,1,0,9,14,4,4,3,7,15,13,3,2,1,0,J Munuera
XX9,13/08/2022,Unknown,Team,1,1,D,0,0,,,,,,,,,,,,,
E0,13/08/2022,Fulham,Liverpool,,,,,,,,,,,,,,,,,,
"""


def test_parses_valid_rows_and_counts_malformed():
    matches, malformed = parse_football_data_uk_csv(CSV)
    # Two valid rows (E0 + SP1). The XX9 row has an unknown division and the last
    # row has no goals, so both are malformed and skipped, not coerced.
    assert len(matches) == 2
    assert malformed == 2


def test_competition_mapping_and_result():
    matches, _ = parse_football_data_uk_csv(CSV)
    palace = matches[0]
    assert palace.competition_code == "EPL"
    assert palace.result == "A"
    assert palace.away_shots == 12
    assert palace.home_reds == 0
    osasuna = matches[1]
    assert osasuna.competition_code == "LALIGA"
    assert osasuna.away_reds == 0
    assert osasuna.home_reds == 1


def test_season_derivation_from_august_date():
    matches, _ = parse_football_data_uk_csv(CSV)
    # August 2022 belongs to the 2022-2023 season.
    assert matches[0].season == "2022-2023"


def test_unique_key_is_stable_and_distinct():
    matches, _ = parse_football_data_uk_csv(CSV)
    keys = {m.unique_key() for m in matches}
    assert len(keys) == 2
    assert "EPL|2022-2023|2022-08-12|Crystal Palace|Arsenal" in keys
