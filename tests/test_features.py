"""Feature registry, shot features, and leakage audit oracles."""

from datetime import date

from touchline.domain.clock import MatchClock, PeriodKind
from touchline.domain.events import BodyPart, Shot
from touchline.domain.geometry import PITCH_LENGTH_M, Point
from touchline.domain.identifiers import Provider, TeamId
from touchline.features.leakage import audit_features, audit_split_groups
from touchline.features.registry import (
    Availability,
    FeatureRegistry,
    FeatureSpec,
    FeatureValue,
    KnowledgeTime,
)
from touchline.features.shots import shot_features


def _shot(x, y, goal=False, pen=False, freeze=None, body=BodyPart.RIGHT_FOOT):
    return Shot(
        event_index=0,
        clock=MatchClock(PeriodKind.FIRST_HALF, 600),
        team=TeamId(Provider.STATSBOMB, "1"),
        player=None,
        location=Point(x, y),
        body_part=body,
        is_penalty=pen,
        is_shootout=False,
        is_goal=goal,
        raw={"freeze_frame": freeze} if freeze is not None else {},
    )


def test_shot_features_dense_vector_shape_and_values():
    x = 1.0 - 11.0 / PITCH_LENGTH_M
    row = shot_features(_shot(x, 0.5, pen=True))
    v = row.dense_vector()
    assert len(v) == 7
    assert row.is_penalty == 1
    assert row.has_spatial == 0
    assert row.defenders_in_cone is None


def test_spatial_features_only_with_freeze_frame():
    ff = [
        {"location": [118, 40], "teammate": False, "position": {"name": "Goalkeeper"}},
        {"location": [116, 41], "teammate": False, "position": {"name": "Center Back"}},
    ]
    row = shot_features(_shot(0.9, 0.5, freeze=ff))
    assert row.has_spatial == 1
    assert row.defenders_in_cone is not None
    assert row.gk_distance_m is not None


def test_post_match_feature_cannot_inform_in_match_origin_same_date():
    reg = FeatureRegistry()
    final_pos = reg.register(
        FeatureSpec("final_league_position", "team", Availability.POST_MATCH)
    )
    d = date(2022, 5, 1)
    fv = FeatureValue(
        final_pos,
        value=4,
        knowledge=KnowledgeTime(d, None, Availability.POST_MATCH),
    )
    origin = KnowledgeTime(d, MatchClock(PeriodKind.FIRST_HALF, 300), Availability.IN_MATCH)
    findings = audit_features(reg, [fv], origin)
    assert len(findings) == 1
    assert findings[0].feature_name == "final_league_position"


def test_prior_date_feature_is_usable():
    reg = FeatureRegistry()
    elo = reg.register(FeatureSpec("prior_elo", "team", Availability.PRE_MATCH))
    fv = FeatureValue(
        elo,
        1500.0,
        KnowledgeTime(date(2022, 4, 1), None, Availability.PRE_MATCH),
    )
    origin = KnowledgeTime(date(2022, 5, 1), None, Availability.PRE_MATCH)
    assert audit_features(reg, [fv], origin) == []


def test_in_match_feature_respects_clock():
    reg = FeatureRegistry()
    spec = reg.register(FeatureSpec("score_diff", "match", Availability.IN_MATCH))
    d = date(2022, 5, 1)
    late = FeatureValue(
        spec, -1, KnowledgeTime(d, MatchClock(PeriodKind.SECOND_HALF, 80 * 60), Availability.IN_MATCH)
    )
    early_origin = KnowledgeTime(
        d, MatchClock(PeriodKind.FIRST_HALF, 10 * 60), Availability.IN_MATCH
    )
    # A score difference known at minute 80 cannot inform a minute-10 prediction.
    assert len(audit_features(reg, [late], early_origin)) == 1


def test_split_group_overlap_detected():
    findings = audit_split_groups({"EPL|2021-2022"}, {"EPL|2021-2022", "UCL|2021-2022"})
    assert len(findings) == 1
    assert findings[0].feature_name == "EPL|2021-2022"
