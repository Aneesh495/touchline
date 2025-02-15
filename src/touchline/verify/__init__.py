"""Independent verification of evidence bundles.

The verifier is implemented separately from whatever produced the results. It
recomputes decisive quantities from raw records and performs bounded replay with
the saved artifacts, rather than trusting any pass flag written into the bundle.
Its semantic negative controls deliberately corrupt a copy of an evidence bundle
in a meaningful way (future-feature leakage, flipped pitch direction, altered goal
labels, an impossible qualification state) and confirm the verifier rejects for a
semantic reason, not merely a hash mismatch.
"""

from touchline.verify.checks import (
    check_goal_labels_consistent,
    check_no_future_features,
    check_pitch_direction,
    check_qualification_possible,
)

__all__ = [
    "check_no_future_features",
    "check_pitch_direction",
    "check_goal_labels_consistent",
    "check_qualification_possible",
]
