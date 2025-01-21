"""Chronological, leakage-aware feature construction.

The central discipline of this layer is knowledge time. Every feature records the
moment its value became known. A feature may only be used to predict an event
whose prediction origin is at or after the feature's knowledge time. This makes
leakage a type error rather than a subtle bug: the final league position of a
season cannot be a feature for a match played in that season, and a substitution
in minute 80 cannot inform a prediction made at minute 10.

The :class:`FeatureRegistry` enforces this, and the leakage audit in
:mod:`touchline.features.leakage` turns the rule into a test.
"""

from touchline.features.registry import (
    FeatureRegistry,
    FeatureSpec,
    FeatureValue,
    KnowledgeTime,
)
from touchline.features.shots import ShotFeatureRow, shot_features

__all__ = [
    "FeatureRegistry",
    "FeatureSpec",
    "FeatureValue",
    "KnowledgeTime",
    "shot_features",
    "ShotFeatureRow",
]
