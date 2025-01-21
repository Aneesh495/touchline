"""Leakage audit over a set of features and a prediction origin.

Given the features a model intends to use and the origin at which it will predict,
the audit reports any feature whose knowledge time does not precede the origin.
It also detects split-crossing: a training example whose match belongs to a
group (competition-season) that also appears in the test set, which would leak
information across the chronological boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

from touchline.features.registry import FeatureRegistry, FeatureValue, KnowledgeTime


@dataclass(frozen=True)
class LeakageFinding:
    feature_name: str
    reason: str


def audit_features(
    registry: FeatureRegistry,
    features: list[FeatureValue],
    origin: KnowledgeTime,
) -> list[LeakageFinding]:
    """Return findings for any feature not knowable at the origin."""
    findings: list[LeakageFinding] = []
    for fv in features:
        if not registry.check_usable(fv, origin):
            findings.append(
                LeakageFinding(
                    fv.spec.name,
                    f"knowledge time ({fv.knowledge.availability.value}, "
                    f"{fv.knowledge.match_date}) does not precede origin "
                    f"({origin.availability.value}, {origin.match_date})",
                )
            )
    return findings


def audit_split_groups(
    train_groups: set[str], test_groups: set[str]
) -> list[LeakageFinding]:
    """Detect competition-season groups that appear in both train and test."""
    overlap = train_groups & test_groups
    return [
        LeakageFinding(g, "group appears in both train and test splits")
        for g in sorted(overlap)
    ]
