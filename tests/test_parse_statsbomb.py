"""StatsBomb parser oracles using schema-faithful fixtures.

Fixtures mirror the real open-data schema (verified against the published files)
but are small and hand-built so the expected canonical output is reasoned
independently of the parser.
"""

import json

from touchline.domain.clock import PeriodKind
from touchline.domain.events import BodyPart, EventType
from touchline.parse.statsbomb import (
    parse_statsbomb_competitions,
    parse_statsbomb_events,
)


def test_competitions_parse_and_detect_360():
    data = json.dumps(
        [
            {
                "competition_id": 16,
                "season_id": 4,
                "competition_name": "Champions League",
                "season_name": "2018/2019",
                "country_name": "Europe",
                "match_available_360": None,
            },
            {
                "competition_id": 9,
                "season_id": 281,
                "competition_name": "1. Bundesliga",
                "season_name": "2023/2024",
                "country_name": "Germany",
                "match_available_360": "2025-11-15T23:17:41",
            },
        ]
    )
    comps = parse_statsbomb_competitions(data)
    assert len(comps) == 2
    assert comps[0].has_360 is False
    assert comps[1].has_360 is True


def test_shot_canonicalisation_and_goal_flag():
    events_json = json.dumps(
        [
            {
                "index": 10,
                "period": 1,
                "minute": 20,
                "second": 5,
                "type": {"name": "Shot"},
                "team": {"id": 206, "name": "Alaves"},
                "player": {"id": 123, "name": "Striker"},
                "possession": 7,
                "play_pattern": {"name": "Regular Play"},
                "location": [114.0, 40.0],
                "shot": {
                    "outcome": {"name": "Goal"},
                    "body_part": {"name": "Right Foot"},
                    "type": {"name": "Open Play"},
                },
            }
        ]
    )
    events, shots = parse_statsbomb_events(events_json, home_team_id=206)
    assert len(shots) == 1
    s = shots[0]
    assert s.is_goal is True
    assert s.is_penalty is False
    assert s.body_part is BodyPart.RIGHT_FOOT
    # Shot from x=114/120 is close to goal; canonical distance should be small.
    assert s.location.distance_to_goal_m() < 12.0
    assert events[0].type is EventType.SHOT


def test_penalty_and_shootout_separation():
    events_json = json.dumps(
        [
            {
                "index": 1,
                "period": 2,
                "minute": 70,
                "second": 0,
                "type": {"name": "Shot"},
                "team": {"id": 1, "name": "A"},
                "location": [108.0, 40.0],
                "shot": {
                    "outcome": {"name": "Saved"},
                    "type": {"name": "Penalty"},
                    "body_part": {"name": "Left Foot"},
                },
            },
            {
                "index": 2,
                "period": 5,
                "minute": 0,
                "second": 0,
                "type": {"name": "Shot"},
                "team": {"id": 1, "name": "A"},
                "location": [108.0, 40.0],
                "shot": {
                    "outcome": {"name": "Goal"},
                    "type": {"name": "Penalty"},
                    "body_part": {"name": "Right Foot"},
                },
            },
        ]
    )
    _, shots = parse_statsbomb_events(events_json, home_team_id=1)
    regulation_pen = shots[0]
    shootout_pen = shots[1]
    assert regulation_pen.is_penalty and not regulation_pen.is_shootout
    assert regulation_pen.counts_toward_regulation is True
    assert shootout_pen.is_shootout and shootout_pen.counts_toward_regulation is False
    assert shootout_pen.clock.period is PeriodKind.SHOOTOUT


def test_stoppage_time_split():
    events_json = json.dumps(
        [
            {
                "index": 1,
                "period": 1,
                "minute": 47,  # 45 + 2 stoppage
                "second": 0,
                "type": {"name": "Pass"},
                "team": {"id": 1, "name": "A"},
                "location": [50.0, 40.0],
            }
        ]
    )
    events, _ = parse_statsbomb_events(events_json, home_team_id=1)
    c = events[0].clock
    assert c.period is PeriodKind.FIRST_HALF
    assert c.added == 2 * 60
    assert c.display() == "45+2"
