"""Semantic checks the verifier recomputes from raw records.

Each check recomputes a property from the underlying data and returns a list of
reasons it failed (empty when it passes). These are the checks the negative
controls target: they must catch a leakage, a flipped pitch, an altered label, and
an impossible qualification, and they do so by recomputation rather than by reading
a stored boolean.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def check_no_future_features(feature_records: list[dict[str, Any]]) -> list[str]:
    """Each record declares a knowledge date and a prediction-origin date.

    A record leaks if its feature became known on or after the origin it informs,
    unless it is explicitly a pre-match feature from a prior date. This recomputes
    the comparison from the dates in the raw records.
    """
    reasons: list[str] = []
    for r in feature_records:
        kd = _as_date(r.get("knowledge_date"))
        od = _as_date(r.get("origin_date"))
        avail = r.get("availability", "pre_match")
        if kd is None or od is None:
            continue
        if avail == "post_match" and kd >= od:
            reasons.append(
                f"feature {r.get('name')!r} is post-match (known {kd}) "
                f"but informs origin {od}"
            )
        elif avail != "post_match" and kd > od:
            reasons.append(
                f"feature {r.get('name')!r} known {kd} after origin {od}"
            )
    return reasons


def check_pitch_direction(shot_records: list[dict[str, Any]]) -> list[str]:
    """Shots should cluster near the attacking goal (canonical x near 1).

    A flipped pitch pushes the mean shot x toward 0. We recompute the mean
    canonical x of shots and flag a direction error when goals and shots sit in the
    defensive half, which is physically implausible for shot locations.
    """
    reasons: list[str] = []
    xs = [r["canonical_x"] for r in shot_records if "canonical_x" in r]
    if not xs:
        return reasons
    mean_x = sum(xs) / len(xs)
    if mean_x < 0.5:
        reasons.append(
            f"mean shot x {mean_x:.3f} < 0.5: shots are in the defensive half, "
            "pitch direction is likely flipped"
        )
    return reasons


def check_goal_labels_consistent(shot_records: list[dict[str, Any]]) -> list[str]:
    """The goal count implied by shot labels must match the recorded score.

    Each record carries ``is_goal`` and the match's recorded goals for that team.
    Summing the goal labels per match-team must equal the recorded score; an
    altered label breaks this identity.
    """
    reasons: list[str] = []
    tally: dict[tuple[str, str], int] = {}
    recorded: dict[tuple[str, str], int] = {}
    for r in shot_records:
        key = (r.get("match_id"), r.get("team"))
        if r.get("is_shootout"):
            continue
        tally[key] = tally.get(key, 0) + int(bool(r.get("is_goal")))
        recorded[key] = r.get("recorded_goals", recorded.get(key, 0))
    for key, n in tally.items():
        if key in recorded and n != recorded[key]:
            reasons.append(
                f"match {key[0]} team {key[1]}: {n} goal labels != "
                f"{recorded[key]} recorded goals"
            )
    return reasons


def check_qualification_possible(sim_records: list[dict[str, Any]]) -> list[str]:
    """No team may be reported as qualifying from an impossible position.

    Each record has a finishing position and a claimed outcome. For a standard
    league, a team finishing below the qualification cutoff cannot be marked as
    qualified. This recomputes the implication from the raw position.
    """
    reasons: list[str] = []
    for r in sim_records:
        pos = r.get("position")
        qualified = r.get("qualified")
        cutoff = r.get("cutoff")
        if pos is None or cutoff is None:
            continue
        if qualified and pos > cutoff:
            reasons.append(
                f"team {r.get('team')} finished {pos} (cutoff {cutoff}) "
                "but is marked qualified"
            )
    return reasons


def _as_date(v: Any) -> date | None:
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v)
        except ValueError:
            return None
    return None
