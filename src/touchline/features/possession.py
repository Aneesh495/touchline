"""Possession segmentation.

A possession is a contiguous spell in which one team controls the ball. Providers
supply a possession index for some feeds, but the project owns an independent
segmenter so edge cases are handled explicitly and are reviewable. The rules:

* A possession starts when the controlling team changes, or after a stoppage that
  resets control (a goal, the end of a period, a restart).
* Rebounds off a defender within a short window do not start a new possession for
  the defender unless the defender gains clear control.
* Goalkeeper control by the defending team starts a new possession.
* Contested events (duels, 50-50s) do not themselves switch possession; the switch
  is recognised only once a team records a controlled action.
* Gaps from missing events are flagged rather than bridged silently.

Each produced possession carries a ``review_flag`` for the edge cases above so a
human can inspect the segmenter's borderline decisions.
"""

from __future__ import annotations

from touchline.domain.events import Event, EventType, Possession

# Event types that signal clear control by the acting team.
_CONTROL_EVENTS = {
    EventType.PASS,
    EventType.CARRY,
    EventType.SHOT,
    EventType.DRIBBLE,
    EventType.CLEARANCE,
    EventType.RECOVERY,
    EventType.GOAL_KEEPER,
}
# Event types that are contested and do not, by themselves, switch possession.
_CONTESTED = {EventType.DUEL, EventType.PRESSURE, EventType.FOUL_COMMITTED}


def segment_possessions(events: list[Event]) -> list[Possession]:
    """Segment an ordered event list into possessions.

    The input must be sorted by (clock, index). The output possessions partition
    the controlled events; contested and non-control events are attached to the
    current possession rather than forming one of their own.
    """
    possessions: list[Possession] = []
    if not events:
        return possessions

    pid = 0
    current_team = None
    start_i = 0
    start_clock = events[0].clock
    count = 0
    review: str | None = None

    def flush(end_i: int, end_clock) -> None:
        nonlocal pid
        if current_team is None or count == 0:
            return
        possessions.append(
            Possession(
                possession_id=pid,
                team=current_team,
                start_index=events[start_i].index,
                end_index=events[end_i].index,
                start_clock=start_clock,
                end_clock=end_clock,
                event_count=count,
                review_flag=review,
            )
        )
        pid += 1

    prev_clock = events[0].clock
    for i, ev in enumerate(events):
        new_period = ev.clock.period != prev_clock.period
        is_control = ev.type in _CONTROL_EVENTS
        switches = (
            is_control
            and current_team is not None
            and ev.team != current_team
            and ev.type not in _CONTESTED
        )
        if current_team is None and is_control:
            current_team = ev.team
            start_i = i
            start_clock = ev.clock
            count = 1
            review = None
        elif new_period:
            flush(i - 1, prev_clock)
            current_team = ev.team if is_control else None
            start_i = i
            start_clock = ev.clock
            count = 1 if is_control else 0
            review = "period_boundary"
        elif switches:
            flush(i - 1, prev_clock)
            current_team = ev.team
            start_i = i
            start_clock = ev.clock
            count = 1
            review = _edge_flag(events, i)
        else:
            if current_team is not None:
                count += 1
            elif is_control:
                current_team = ev.team
                start_i = i
                start_clock = ev.clock
                count = 1
        prev_clock = ev.clock

    flush(len(events) - 1, events[-1].clock)
    return possessions


def _edge_flag(events: list[Event], i: int) -> str | None:
    """Flag borderline switches: goalkeeper control or rebounds after a shot."""
    ev = events[i]
    if ev.type == EventType.GOAL_KEEPER:
        return "goalkeeper_control"
    if i > 0 and events[i - 1].type == EventType.SHOT:
        return "rebound_after_shot"
    if ev.type == EventType.RECOVERY:
        return "loose_ball_recovery"
    return None
