"""Match and possession replay timeline.

The interface replays a match by stepping through events in order, each placed on a
synchronized timeline keyed by the match-monotone second. This module turns a list
of events into a timeline the UI can scrub: each frame carries the event, its
monotone time, the current possession id, and the running score. The timeline is
strictly ordered and every frame's time is non-decreasing.
"""

from __future__ import annotations

from dataclasses import dataclass

from touchline.domain.events import Event, EventType


@dataclass(frozen=True)
class TimelineFrame:
    event_index: int
    monotone_second: int
    display_time: str
    event_type: str
    team: str
    possession_id: int | None
    home_score: int
    away_score: int


def build_timeline(
    events: list[Event], home_team, goal_predicate=None
) -> list[TimelineFrame]:
    """Build a scrubable replay timeline with a running score.

    ``goal_predicate(ev)`` marks an event as a goal; by default a shot whose raw
    payload records a goal outcome counts. The running score updates as goals pass,
    so scrubbing to any frame shows the score at that moment.
    """
    if goal_predicate is None:
        def goal_predicate(ev: Event) -> bool:
            if ev.type is not EventType.SHOT:
                return False
            shot = ev.raw.get("shot", {}) if ev.raw else {}
            outcome = shot.get("outcome", {}) if isinstance(shot, dict) else {}
            return outcome.get("name") == "Goal"

    frames: list[TimelineFrame] = []
    home_score = 0
    away_score = 0
    last_t = -1
    for ev in sorted(events, key=lambda e: (e.clock, e.index)):
        if goal_predicate(ev):
            if ev.team == home_team:
                home_score += 1
            else:
                away_score += 1
        t = ev.clock.monotone_second()
        # enforce non-decreasing timeline
        t = max(t, last_t)
        last_t = t
        frames.append(
            TimelineFrame(
                event_index=ev.index,
                monotone_second=t,
                display_time=ev.clock.display(),
                event_type=ev.type.value,
                team=str(ev.team.value),
                possession_id=ev.possession_id,
                home_score=home_score,
                away_score=away_score,
            )
        )
    return frames
